import atexit
import pprint
import signal
from abc import abstractmethod
from copy import copy
from functools import wraps

import pendulum

import py_stealth as stealth
from tools import constants, tools
from tools.tools import log
from .container import Container
from .item import Item
from .mob import Mob
from .player import Player, alive_action

BANK_COORDS = (2512, 556)
HEALER_COORDS = constants.COORDS_MINOC_HEALER
BANK_ID = 0x7277EC74


def condition(condition_):
    def real_decorator(func):
        @wraps(func)
        def requires_constant_wrapper(self, *args, **kwargs):
            if not condition_:
                return 666

            result = func(self, *args, **kwargs)
            return result

        return requires_constant_wrapper

    return real_decorator


class ScriptBase:
    def __init__(self):
        self.scenario_name = self.__class__.__name__
        self.player = Player()
        self._start_time = None
        self._processed_mobs = []
        self.script_stats = {}
        self._register_signals()
        self.commands_cooldown_sec = 30
        self._commands_cooldown = {}
        self._looted_corpses = []
        self._checked_weapons = []
        self.commands_journal_index = stealth.HighJournal()
        self.loot_container = None
        self.unload_itemids = []
        self.tool_typeid = None
        atexit.register(self.at_exit)

    def _register_signals(self):
        signals = (signal.SIGABRT, signal.SIGBREAK, signal.SIGFPE, signal.SIGILL, signal.SIGINT, signal.SIGSEGV,
                   signal.SIGTERM)
        for signal_ in signals:
            signal.signal(signal_, self.at_exit)

    def at_exit(self):
        log.info(f"{self} atexit.")
        self.print_script_stats()

    def print_script_stats(self):
        log.info(f"{self} stats:")
        msg = self.script_stats_str
        for line in msg.split('\n'):
            if not line:
                continue

            log.info(f"  {line}")

    def __str__(self):
        return self.name

    def stop(self):
        log.info(f"Stopping {self}")
        self.at_exit()
        stealth.StopAllScripts()

    def _parse_command(self, command, start_index=None, journal_lines=None):
        return tools.in_journal(f'{self.player.name}: {command}', from_index=start_index, journal_lines=journal_lines) \
               and not self._commmand_on_cooldown(command)

    def _commmand_on_cooldown(self, command):
        record = self._commands_cooldown.get(command)
        if not record:
            return False

        return pendulum.now() <= record

    def _command_add_cooldown(self, command, cooldown_secs=None):
        if cooldown_secs is None:
            cooldown_secs = self.commands_cooldown_sec

        self._commands_cooldown[command] = pendulum.now().add(seconds=cooldown_secs)

    def report_stats(self):
        self.print_script_stats()

    def parse_commands(self):
        journal = tools.journal(start_index=self.commands_journal_index)
        if self._parse_command('quit', journal_lines=journal):
            self._command_add_cooldown('quit')
            return self.quit()
        elif self._parse_command('stop', journal_lines=journal):
            self._command_add_cooldown('stop')
            return self.stop()
        elif self._parse_command('stats', journal_lines=journal):
            self._command_add_cooldown('stats')
            return self.report_stats()

        self.commands_journal_index = stealth.HighJournal()

    @property
    def script_stats_str(self):
        msg = ''
        for key, value in self.script_stats.items():
            msg += f'\n{key}: {value}'
        return msg

    @property
    def name(self):
        return self.__class__.__name__

    @alive_action
    def wait_stamina(self, threshold=20):
        if self.player.stamina < threshold:
            log.info(f"Waiting stamina at least {threshold}")
        else:
            return

        while self.player.alive and self.player.stamina < threshold:
            tools.result_delay()
        log.info(f"Stamina reached {threshold}")

    @alive_action
    def pick_up_items(self, type_ids):
        found_items = self.player.find_types_ground(type_ids, distance=constants.MAX_PICK_UP_DISTANCE)
        for item in found_items:
            self.player.grab(item)

    @alive_action
    def engage_mob(self, mob: Mob, check_health_func=None, loot=False, cut=False, drop_trash_items=True,
                   notify_only_mutated=not log.verbose, trash_items=None):
        check_health_func = check_health_func or self.check_health
        if not mob.exists:
            log.debug(f"Won't engage nonexisting {mob}")
            return

        if mob.dead:
            log.debug(f"Won't engage dead {mob}")
            return

        # distance = mob.path_distance()  # this is being checked before this function
        # if distance > 50:
        #     log.info(f"Won't engage mob that {distance} this far away")
        #     return

        log.info(f"Engaging {mob.hp}/{mob.max_hp} {mob} at distance {mob.distance}")
        if mob.mutated:
            stealth.Alarm()
        while mob.alive:
            if mob.distance > 1:
                self.player.move(mob.x, mob.y)
                self.player.attack(mob.id_)
            else:
                log.info(f"Won't engage {mob} that is already at distance {mob.distance}")
            check_health_func()  # script_check_health in scripts
        log.info(f"Done Engaging {mob}")
        self.player.war_mode = False
        if not notify_only_mutated or (notify_only_mutated and mob.mutated):
            tools.telegram_message(f"{mob} dead", disable_notification=not mob.mutated)
        if loot:
            self.player.break_action()
            self.player.loot_nearest_corpse(cut_corpse=cut, drop_trash_items=drop_trash_items)
            self.drop_trash(trash_items=trash_items)

    @alive_action
    def drop_trash(self, trash_items=None):
        trash_items = trash_items or constants.ITEM_IDS_TRASH
        return self.player.drop_trash_items(trash_items)

    @alive_action
    def loot_corpses(self, drop_trash_items=True, trash_items=None, cut_corpses=True, corpse_find_distance=2):
        corpses = [
            Container.instantiate(i)
            for i in self.player.find_types_ground(constants.TYPE_ID_CORPSE, distance=corpse_find_distance)
        ]
        for corpse in corpses:
            if corpse in self._looted_corpses:
                continue

            self.player.loot_nearest_corpse(corpse_id=corpse, cut_corpse=cut_corpses, drop_trash_items=drop_trash_items,
                                            trash_items=trash_items)
            self._looted_corpses.append(corpse)
        self.player.drop_trash_items(trash_item_ids=trash_items)

    @alive_action
    def check_overweight(self, drop_types=None):
        if not self.player.overweight:  # consider near_max_weight
            return

        self.player.break_action()
        self.drop_trash()
        self.drop_overweight_items(drop_types=drop_types)

    @alive_action
    def drop_overweight_items(self, drop_types):
        if not drop_types:
            return

        for drop_type, drop_color, drop_weight in drop_types:
            weight_drop_needed = self.player.weight - self.player.max_weight
            if weight_drop_needed < 1:
                break

            while True:
                weight_drop_needed = self.player.weight - self.player.max_weight
                if weight_drop_needed < 1:
                    break

                drop_object_id = self.player.find_type_backpack(drop_type, drop_color)
                if not drop_object_id:
                    break

                drop_item = Item.instantiate(drop_object_id, color=drop_color, weight=drop_weight, omit_cache=True)
                if not drop_item.quantity:
                    break

                drop_quantity = min((weight_drop_needed // drop_item.weight_one) + 1, drop_item.quantity)
                if not drop_quantity:
                    log.info(f"won't drop {drop_quantity} of {drop_item.name} {drop_object_id}")
                    break

                log.info(f"Need to relieve of {weight_drop_needed}st. Dropping {drop_quantity}×{drop_item}")
                drop_result = self.player.drop_item(drop_item, drop_quantity)
                if drop_result:
                    log.info(f"Drop successful")
                    tools.result_delay()
                    break

    def quit(self, alarm=True):
        if alarm:
            stealth.Alarm()
        log.info("Quitting")
        tools.telegram_message(f"{self.player} quitting")
        self.at_exit()
        self.disconnect()
        exit()

    @staticmethod
    def disconnect():
        stealth.SetARStatus(False)
        stealth.Disconnect()
        stealth.CorrectDisconnection()

    @property
    def script_running_time(self):
        script_running_time = pendulum.now() - self._start_time
        return script_running_time

    @property
    def script_running_time_words(self):
        return self.script_running_time.in_words()

    def resurrect(self):
        log.info(f"Resurrecting and returning")
        self._processed_mobs = []
        while self.player.dead:
            log.info(f"Moving to healer {HEALER_COORDS}")
            self.player.move(*HEALER_COORDS, accuracy=0)
        reagent_types = [constants.TYPE_ID_REAGENT_MR, constants.TYPE_ID_REAGENT_BM, constants.TYPE_ID_REAGENT_BP]
        while len(regs := self.player.find_types_backpack(reagent_types)) < 3 or self.player.xy == BANK_COORDS:
            if self.player.xy != BANK_COORDS:
                log.info(f"Moving to bank @ {BANK_COORDS}")
                self.player.move(*BANK_COORDS, accuracy=0)
            bank = Container.instantiate(BANK_ID)
            if bank.is_empty:
                log.info(f"Opening bank")
                self.player.say('bank')
                tools.result_delay()
                self.player.hide()
            if self.player.xy == BANK_COORDS:
                log.info(f"Grabbing reagents {reagent_types}")
                for reg_type in reagent_types:
                    if self.player.got_item_type(reg_type):
                        continue

                    bank_item = self.player.find_type(reg_type, bank)
                    if not bank_item:
                        log.info(f"No reagent {reg_type} found @ bank")
                        tools.telegram_message(f"Couldn't resurrect. No reagent {reg_type} found @ bank")
                        self.disconnect()
                        quit()
                    grab_result = self.player.grab(bank_item, quantity=1)
                    if not grab_result:
                        log.info(f"Couldn't grab {reg_type}:{bank_item} from bank")
                        tools.telegram_message(f"Couldn't resurrect. Couldn't grab {reg_type}:{bank_item} from bank")
                        self.disconnect()
                        quit()

                rune = self.player.find_type(constants.TYPE_ID_RUNE, bank)
                if rune:
                    log.info(f"Casting Recall @ {rune}")
                    stealth.CastToObject('recall', rune)
                    stealth.Wait(5000)
                    if self.player.xy != BANK_COORDS:
                        break
                else:
                    log.info(f"No rune found @ bank")
                    tools.telegram_message("Couldn't resurrect. No rune found @ bank")
                    self.disconnect()
                    quit()

        self.move_to_unload()
        self.unload()

    def move_to_unload(self, loot_container=None):
        loot_container = loot_container or self.loot_container
        self.parse_commands()
        if self.player.path_distance_to(*loot_container.xy) > 1:
            log.info("Moving to unload")
            self.wait_stamina()
            self.player.move(*loot_container.xy, accuracy=0)
            log.info("Moving to unload done")
        tools.ping_delay()
        self.player.open_container(loot_container)

    def record_stats(self):
        pass

    def checks(self):
        pass

    def move_to_spot_loop(self, spot_x, spot_y):
        log.debug(f"Entering {tools.get_function_name()}")
        self.checks()
        while self.player.distance_to(spot_x, spot_y) > 0:
            log.info(f"Moving to spot: {spot_x} {spot_y}")
            self.wait_stamina(5)
            self.player.move(spot_x, spot_y, accuracy=0, running=self.should_run)
            self.checks()
        log.debug(f"Exiting {tools.get_function_name()}")

    def overweight_loop(self):
        while self.player.overweight:  # consider near_max_weight
            log.debug(f"Entering {tools.get_function_name()} loop")
            self.parse_commands()
            self.check_overweight()
            if self.player.overweight:
                coords = self.player.xy
                self.move_to_unload()
                self.unload()
                self.move_to_spot_loop(*coords)
        log.debug(f"Exiting {tools.get_function_name()} loop")

    def unload_get_tool(self, tool_typeid=None, loot_container=None):
        tool_typeid = tool_typeid or self.tool_typeid
        if not tool_typeid:
            log.critical(f"You should define self.tool_typeid")
            return

        got_tool = self.player.find_types(tool_typeid)
        if got_tool:
            return

        log.debug(f"{tools.get_function_name()}")
        loot_container = loot_container or self.loot_container
        container_tool = self.player.find_type(tool_typeid, loot_container)
        if not container_tool:
            todo = stealth.GetFindedList()
            log.info("WARNING! NO SPARE TOOLS FOUND!")
            tools.telegram_message(f"{self.player}: {self.name}: No tools found: {todo}")
            self.quit()
            return

        while not self.player.find_types(tool_typeid) and not self.player.move_item(container_tool):
            log.info(f"Grabbing Tool {container_tool}")
            tools.ping_delay()
        log.debug(f"{tools.get_function_name()} done")

    def unload(self):
        log.info("Unloading")
        self.move_to_unload()
        self.record_stats()
        self.parse_commands()
        self.player.unload_types(self.unload_itemids, self.loot_container)
        self.unload_get_tool()
        self.check_bandages()
        self.rearm_from_container()
        self.eat()
        self._processed_mobs = []
        self.report_stats()

    def check_health(self, resurrect=False):
        if self.player.dead:
            if resurrect:
                tools.telegram_message(f'{self.player} is dead. Script ran for {self.script_running_time_words}. '
                                       f'Resurrecting.')
                self.resurrect()
            else:
                tools.telegram_message(f'{self.player} is dead. Script ran for {self.script_running_time_words}')
                self.player.move(*constants.COORDS_MINOC_HEALER)
                self.quit()

        if not self.player.got_bandages:
            return False

        need_heal = (self.player.max_hp - self.player.hp) > (self.player.max_hp * 0.4)
        if need_heal:
            if self.player.got_bandages:
                self.player.break_action()
                self.player.bandage_self_if_hurt()
                return True
            else:
                return False
        else:
            return True

    @alive_action
    def got_bandages(self, quantity):
        return stealth.GetQuantity(self.player.find_type_backpack(constants.TYPE_ID_BANDAGE)) == quantity

    @alive_action
    def _check_bandages(self, quantity, container_id):
        log.info("Checking Bandages")
        container = Container.instantiate(container_id)
        player_bandages = self.player.got_bandages
        if not player_bandages or stealth.GetQuantity(player_bandages) < quantity:
            bandages = self.player.find_type(constants.TYPE_ID_BANDAGE, container)
            if not bandages:
                log.info("WARNING! NO SPARE BANDAGES FOUND!")
                tools.telegram_message(f"{self.player}: No bandages found. "
                                       f"Script ran for {self.script_running_time_words}")
                self.quit()
                return

            while not self.got_bandages(quantity) and not self.player.move_item(bandages, quantity):
                log.info("Grabbing Bandages")
                tools.ping_delay()

    @alive_action
    def eat(self, container_id, food_type=None):
        food_type = food_type or constants.TYPE_ID_FOOD_FISHSTEAKS
        self.player.open_container(container_id)
        log.info("Eating")
        food = self.player.find_type(food_type, container_id)
        if not food:
            log.info("WARNING! NO FOOD FOUND!")
            tools.telegram_message(f"{self.player}: No food found", disable_notification=True)
            return

        food = Item.instantiate(food)
        self.player.use_object(food)

    @alive_action
    def process_mobs(self, engage=True, notify_mutated=True, notify_ranged=True, notify_errors=True,
                     mob_find_distance=20, drop_overweight_items=None):
        output = False
        while creatures := self.player.find_creatures(
                distance=mob_find_distance, notorieties=[constants.Notoriety.Murderer],
                condition=lambda i: i not in self._processed_mobs
                                    and i.exists and not i.dead and not i.mount and not i.human):
            for creature in creatures:
                # noinspection PyProtectedMember
                mob = Mob.instantiate(creature.id_, omit_cache=True)
                if mob in self._processed_mobs:
                    log.debug(f"Skipping processed {mob}")
                    continue

                if mob.dead:
                    log.debug(f"Skipping dead {mob}")
                    self._processed_mobs.append(mob)
                    continue

                # notify = (notify_mutated and mob.mutated) or (
                #             notify_ranged and mob.type_id in constants.TYPE_IDS_MOB_RANGED)
                mob_path_distance = mob.path_distance()
                # if notify:
                #     tools.telegram_message(f"{mob} detected at distance {mob.path_distance()}",
                #                            disable_notification=not mob.mutated)
                if engage:
                    # noinspection PyProtectedMember
                    max_distance = constants.ENGAGE_MAX_DISTANCE
                    if mob_path_distance <= 1:
                        log.debug(f"Already at {mob} at distance path {mob_path_distance}")
                    elif mob_path_distance > max_distance:
                        msg = f"Won't engage {mob}. Distance path: {mob_path_distance}, max distance: {max_distance}"
                        log.debug(msg)
                        # tools.telegram_message(msg)
                    else:
                        if drop_overweight_items:
                            self.drop_overweight_items(drop_overweight_items)
                        self.engage_mob(mob)
                        # if notify:
                        #     dead = mob.dead
                        #     tools.telegram_message(f"Done engaging {mob}. Dead: {dead}", disable_notification=dead)
                        output = True
        return output

    @alive_action
    def rearm_from_container(self, weapon_type_ids=None, container_id=None):
        if self.player.weapon_equipped:
            return

        container = Container.instantiate(container_id)
        log.info(f"Rearming from {container}")
        weapon_type_ids = weapon_type_ids or constants.TYPE_IDS_WEAPONS
        if not weapon_type_ids:
            return

        if not container.exists or not container.is_container:
            return

        for weapon_type_id in weapon_type_ids:
            if self.player.weapon_equipped:
                break

            found_weapon = self.player.find_type(weapon_type_id, container)
            if not found_weapon:
                continue

            self.player.equip_object(found_weapon, stealth.RhandLayer())
            tools.result_delay()

    @alive_action
    def check_weapon(self, max_weapon_search_distance=20):
        if self.player.weapon_equipped:
            return False

        log.info(f"Checking weapons on ground")
        weapon_types = copy(constants.TYPE_IDS_WEAPONS)
        while not self.player.weapon_equipped:
            if not weapon_types:
                log.info(f"No weapons found on ground")
                return

            for weapon_type in weapon_types:
                if self.player.weapon_equipped:
                    return True

                found_weapon = self.player.find_type_ground(weapon_type, distance=max_weapon_search_distance)
                if not found_weapon:
                    weapon_types.remove(weapon_type)
                    continue

                found_weapon = Item.instantiate(found_weapon)
                if found_weapon in self._checked_weapons:
                    weapon_types.remove(weapon_type)
                    continue

                self._checked_weapons.append(found_weapon)
                path_distance = self.player.path_distance_to(*found_weapon.xy)
                if path_distance > max_weapon_search_distance:
                    weapon_types.remove(weapon_type)
                    continue

                self.wait_stamina()
                self.check_overweight()
                self.player.move(*found_weapon.xy, accuracy=constants.MAX_PICK_UP_DISTANCE, running=self.should_run)
                self.player.equip_weapon_id(found_weapon)
                tools.result_delay()
                weapon_types.remove(weapon_type)
                return True

        log.info(f"Done checking weapons on ground")

    @staticmethod
    def mob_type_ids(ranged=False, melee=False, critter=False, aggressive=False):
        mob_type_ids = []
        if ranged:
            mob_type_ids.extend(constants.TYPE_IDS_MOB_RANGED)
        if aggressive:
            mob_type_ids.extend(constants.TYPE_IDS_MOB_AGGRESSIVE)
        if melee:
            mob_type_ids.extend(constants.TYPE_IDS_MOB_MELEE)
        if critter:
            mob_type_ids.extend(constants.TYPE_IDS_CRITTER)
        return mob_type_ids

    @property
    def should_run(self):
        if self.player.dead:
            return True

        return self.player.near_max_weight is False and self.player.stamina > 10
