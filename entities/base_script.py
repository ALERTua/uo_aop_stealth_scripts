import atexit
import random
import signal
from copy import copy
from functools import wraps
from typing import Iterable

import pendulum

import py_stealth as stealth
from tools import constants, tools
from tools.tools import log
from .statistics import cache as statistics_cache, StatRecord, StatRecorder
from .base_creature import Creature
from .base_weapon import WeaponBase, Weapon
from .container import Container
from .item import Item
from .mob import Mob
from .player import Player, alive_action, bandage_cd

BANK_COORDS = (2512, 556)
HEALER_COORDS = constants.COORDS_MINOC_HEALER


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
        self.unload_itemids = constants.TYPE_IDS_LOOT
        self.tool_typeid = None
        self.trash_item_ids = constants.ITEM_IDS_TRASH
        self._hold_bandages = 2
        atexit.register(self.at_exit)

    def _register_signals(self):
        signals = (signal.SIGABRT, signal.SIGBREAK, signal.SIGFPE, signal.SIGILL, signal.SIGINT, signal.SIGSEGV,
                   signal.SIGTERM)
        for signal_ in signals:
            signal.signal(signal_, self.at_exit)

    def at_exit(self):
        log.info(f"{self} atexit.")
        self.print_script_stats()

    def start(self):
        log.info(f"Starting {self.scenario_name}")
        self._start_time = pendulum.now()

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
        elif self._parse_command('debug', journal_lines=journal):
            self._command_add_cooldown('debug')
            return tools.debug()

        self.commands_journal_index = stealth.HighJournal()

    @property
    def script_stats_str(self):
        msg = ''
        if statistics_cache:
            for type_id, type_id_records in statistics_cache.items():
                record: StatRecord
                for color, record in type_id_records.items():
                    msg += f'\n{record.name} : {record.quantity}'
        return msg

    @property
    def name(self):
        return self.__class__.__name__

    @alive_action
    def wait_stamina(self, threshold=0.2):
        stamina_threshold = self.player.max_stamina * threshold
        if self.player.stamina < stamina_threshold:
            log.info(f"Waiting stamina at least {stamina_threshold}")
        else:
            return

        while self.player.alive and self.player.stamina < stamina_threshold:
            tools.result_delay()
        log.info(f"Stamina reached {stamina_threshold}")

    @alive_action
    def pick_up_items(self, type_ids=None):
        type_ids = type_ids or self.unload_itemids
        found_items = self.player.find_types_ground(type_ids, distance=constants.MAX_PICK_UP_DISTANCE)
        if found_items:
            for item in found_items:
                self.player.grab(item)

    def mount(self, mount_id=None):
        if self.player.unmounted:
            # noinspection PyProtectedMember
            mount = Creature.instantiate(mount_id or self.player._mount)
            self.player.move_to_object(mount)
            self.player.use_object(mount)

    @alive_action
    def engage_mob_loop(self,  mob: Mob, check_health_func, ranged=False, ranged_weapon: WeaponBase = None,
                        ranged_unmount=True, ranged_keep_distance=8):
        equipped_weapons = []
        rearm = False
        remount = False
        if ranged:
            if not isinstance(ranged_weapon, WeaponBase):
                ranged_weapon = Weapon.instantiate(ranged_weapon)
        i = 0
        max_i = 200
        while mob.alive and (i := i + 1) < max_i:
            # noinspection PyProtectedMember
            if self.player._mount == mob.id_:
                break

            if mob.distance > 100:
                log.info(f"{mob} distance: {mob.distance}. Breaking")
                break

            if ranged:
                self.player.unequip_tools()
                self.player.keep_away(mob.x, mob.y, ranged_keep_distance, accuracy=0, running=None)
                if ranged_unmount and self.player.mounted:
                    # noinspection PyProtectedMember
                    self.player._mount = self.player._mount or stealth.ObjAtLayer(stealth.HorseLayer())
                    self.player.dismount()
                    tools.result_delay()
                    self.player.say('all follow me')
                    remount = True

                if ranged_weapon.id_ not in self.player.equipped_weapons:
                    equipped_weapons = equipped_weapons or self.player.equipped_weapons
                    self.player.disarm()
                    self.player.equip_weapon_id(ranged_weapon)
                    rearm = True

            else:
                while 50 > mob.distance > 1:
                    self.player.move(mob.x, mob.y, accuracy=1, running=self.player.should_run)
            check_health_func()  # script_check_health in scripts
            tools.result_delay()
            self.player.attack(mob.id_)
            log.info(f"({i}/{max_i}) [{self.player.hp}/{self.player.max_hp}] "
                     f"Fight with [{mob.hp}/{mob.max_hp}]{mob} at range {mob.distance}")
        if remount:
            self.mount()
            tools.result_delay()

        if rearm:
            self.player.disarm()
            for weapon in equipped_weapons:
                if weapon:
                    self.player.equip_weapon_id(weapon)
        self.player.war_mode = False

    @alive_action
    def engage_mob(self, mob: Mob, check_health_func=None, loot=False, cut=False, drop_trash_items=True,
                   notify_only_mutated=not log.verbose, trash_items=None, ranged=False,
                   ranged_weapon: WeaponBase = None, ranged_unmount=True, ranged_keep_distance=8):
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

        self.engage_mob_loop(mob, check_health_func=check_health_func, ranged=ranged, ranged_weapon=ranged_weapon,
                             ranged_unmount=ranged_unmount, ranged_keep_distance=ranged_keep_distance)
        log.info(f"Done Engaging {mob}")
        self.player.war_mode = False
        StatRecorder.record(mob)
        # if not notify_only_mutated or (notify_only_mutated and mob.mutated):
        #     tools.telegram_message(f"{mob} dead", disable_notification=not mob.mutated)
        if loot:
            self.player.break_action()
            range_ = constants.USE_GROUND_RANGE
            if ranged:
                range_ = ranged_keep_distance + 1
            self.player.loot_nearest_corpse(cut_corpse=cut, drop_trash_items=drop_trash_items, range_=range_)
            self.drop_trash(trash_items=trash_items)

    @alive_action
    def drop_trash(self, trash_items=None):
        trash_items = trash_items or self.trash_item_ids
        return self.player.drop_trash_items(trash_items)

    @alive_action
    def loot_corpses(self, drop_trash_items=True, trash_items=None, cut_corpses=True, corpse_find_distance=2):
        trash_items = trash_items or self.trash_item_ids
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
    def check_overweight(self, drop_types=None, trash_items=None):
        if not self.player.overweight:  # consider near_max_weight
            return

        drop_types = drop_types or self.unload_itemids
        trash_items = trash_items or self.trash_item_ids
        self.player.break_action()
        self.drop_trash(trash_items=trash_items)
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
                    log.debug(f"Drop successful")
                    # tools.result_delay()
                    break

    def quit(self, message=None, alarm=True):
        if alarm:
            stealth.Alarm()
        log.info("Quitting")
        message = message or f"{self.player} quitting"
        tools.telegram_message(message)
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
            self.player.war_mode = False
            log.info(f"Moving to healer {HEALER_COORDS}")
            self.player.move(*HEALER_COORDS, accuracy=0)
        reagent_types = [constants.TYPE_ID_REAGENT_MR, constants.TYPE_ID_REAGENT_BM, constants.TYPE_ID_REAGENT_BP]
        while len(regs := self.player.find_types_backpack(reagent_types)) < 3 or self.player.xy == BANK_COORDS:
            if self.player.xy != BANK_COORDS:
                log.info(f"Moving to bank @ {BANK_COORDS}")
                self.player.move(*BANK_COORDS, accuracy=0)
            bank = self.player.bank_container
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

                if self.player.need_heal_bandage and (bank_bandage := self.player.find_type(
                        constants.TYPE_ID_BANDAGE, self.player.bank_container)):
                    self.player.use_object_on_object(bank_bandage, self.player)
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
        if self.player.distance_to(*loot_container.xy) > 1 or self.player.path_distance_to(*loot_container.xy) > 1:
            log.info("Moving to unload")
            self.wait_stamina()
            self.player.disarm()
            self.rearm_from_container(container_id=self.player.backpack)
            result = self.player.move_to_object(loot_container, accuracy=0, running=self.should_run)
            log.debug(f"Moving to unload result: {result}")
        tools.ping_delay()
        self.player.open_container(loot_container, subcontainers=True)

    def record_stats(self):
        items = self.player.find_types_backpack(type_ids=self.unload_itemids, recursive=True)
        if not items:
            return

        for item in items:
            items_obj = Item.instantiate(item)
            StatRecorder.record(items_obj)

    def checks(self, break_action=True):
        pass

    def move_to_spot_loop(self, spot_x, spot_y, accuracy=0):
        log.debug(f"Entering {tools.get_function_name()}")
        # self.checks(break_action=False)
        self.overweight_loop()
        i = 0
        while self.player.distance_to(spot_x, spot_y) > accuracy:
            i += 1
            if i > 10:
                log.warning(f"Failed to reach {spot_x}, {spot_y} with accuracy {accuracy} in {i} tries")
                break

            log.info(f"Moving to spot: {spot_x} {spot_y}")
            self.wait_stamina(0.1)
            if not self.player.move(spot_x, spot_y, accuracy=accuracy, running=self.should_run):
                self.player.move(spot_x, spot_y, accuracy=accuracy + 1, running=self.should_run)
            self.checks()
        log.debug(f"Exiting {tools.get_function_name()}")

    def unload_and_return(self):
        pass

    def overweight_loop(self):
        entered = False
        if self.player.overweight:
            log.debug(f"Entering {tools.get_function_name()}")
            entered = True
        while self.player.overweight:  # consider near_max_weight
            self.parse_commands()
            self.check_overweight()
            if self.player.overweight:
                self.unload_and_return()
        if entered:
            log.debug(f"Exiting {tools.get_function_name()}")

    def _unload_get_item(self, typeid, loot_container=None, quantity=1, colors=None, recursive=False,
                         condition: callable = None):
        if not isinstance(typeid, Iterable):
            typeid = [typeid]
        got_item = self.player.find_types_character(typeid, recursive=recursive)
        got_item = [Item.instantiate(i) for i in got_item]
        if got_item and got_item[0].quantity >= quantity:
            return

        log.debug(f"{tools.get_function_name()}")
        loot_container = loot_container or self.loot_container
        container_items = self.player.find_types(types=typeid, container_ids=loot_container, colors=colors)

        if not container_items:
            todo = stealth.GetFindedList()
            log.info(f"WARNING! NO SPARE {typeid} FOUND! {tools.get_prev_function_name()}")
            tools.telegram_message(f"{self.player}: {self.name}: No {typeid} found: {todo}")
            self.quit()
            return

        container_items = [Item.instantiate(i) for i in container_items]
        container_items.sort(key=lambda _: typeid.index(stealth.GetType(_.id_)) and (condition(_) if condition else True))
        container_item = container_items[0]
        loot_quantity = quantity
        if got_item and quantity > 1 and got_item[0].quantity < quantity:
            loot_quantity = quantity - got_item[0].quantity
            loot_quantity = min((container_item.quantity, loot_quantity))

        while not self.player.got_item_quantity(typeid, quantity) \
                and not self.player.move_item(container_item, quantity=loot_quantity):
            log.info(f"Grabbing {loot_quantity}×{container_item}")
            tools.ping_delay()
        log.debug(f"{tools.get_function_name()} done")

    def unload_get_tool(self, tool_typeid=None, loot_container=None):
        tool_typeid = tool_typeid or self.tool_typeid
        return self._unload_get_item(typeid=tool_typeid, loot_container=loot_container)

    def unload_get_weapon(self):
        pass

    def unload(self, item_ids=None, container=None, drink_trash_potions=True):
        item_ids = item_ids or self.unload_itemids
        container = container or self.loot_container
        log.info("Unloading")
        self.move_to_unload()
        self.record_stats()
        self.parse_commands()
        if drink_trash_potions:
            self.drink_trash_potions()
        self.player.disarm()
        self.player.unload_types(item_ids, container)
        self.unload_get_tool()
        self.unload_get_weapon()
        self.check_bandages()
        self.rearm_from_container()
        self.eat()
        self.heal_from_container(container)
        self._processed_mobs = []
        self.report_stats()

    @alive_action
    def heal_from_container(self, container=None):
        container = container or self.loot_container
        if self.player.need_heal_bandage and (bandage := self.player.find_type(constants.TYPE_ID_BANDAGE, container)):
            bandage_cd(self.player.use_object_on_object)(obj=bandage, target=self.player)

    def check_health(self, resurrect=False):
        if self.player.dead:
            # noinspection PyProtectedMember
            tools.delay(15000)  # in case of false-positive at relogin
            if self.player.dead:
                tools.telegram_message(f'{self.player} is dead. Script ran for {self.script_running_time_words}. '
                                       f'Resurrecting.')
                creatures = self.player.find_creatures(distance=30, path_distance=False)
                creatures = [i for i in creatures if i.name and i != self.player]
                creatures_str = ", ".join([f"{'Human' if c.human else 'Non-Human'} {c}" for c in creatures])
                creatures_report = f"Creatures nearby: {creatures_str}"
                tools.telegram_message(creatures_report)
                if resurrect:
                    self.resurrect()
                else:
                    self.player.move(*constants.COORDS_MINOC_HEALER)
                    self.quit()

        if not self.player.got_bandages:
            return False

        if self.player.need_heal_bandage or self.player.need_heal_potion:
            if self.player.got_bandages or self.player.got_heal_potion:
                # self.player.break_action()
                self.player.bandage_self_if_hurt()
                return True
            else:
                return False
        else:
            return True

    @alive_action
    def got_bandages(self, quantity, recursive=False):
        return self.player.got_item_quantity(constants.TYPE_ID_BANDAGE, quantity, recursive=recursive)

    def check_bandages(self, hold_bandages=None, container=None):
        hold_bandages = hold_bandages or self._hold_bandages
        container = container or self.loot_container
        return self._unload_get_item(constants.TYPE_ID_BANDAGE, container, quantity=hold_bandages, recursive=False)

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
    def eat(self, container_id=None, food_type=None):
        container_id = container_id or self.loot_container
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

    def _find_mobs(self, mob_find_distance=20, notorieties=None, creature_types=None, path_distance=True):
        output = self.player.find_creatures(
            distance=mob_find_distance, notorieties=notorieties, creature_types=creature_types,
            condition=lambda i: i.type_id is not None and i not in self._processed_mobs and not i.dead and not i.human
                                and i.alive and not i.dead and not i.mount,
            path_distance=path_distance)
        return output

    @alive_action
    def process_mobs(self, engage=True, notify_mutated=True, notify_ranged=True, notify_errors=True, loot=True,
                     mob_find_distance=13, drop_overweight_items=None, ranged=False, check_health_func=None, cut=True,
                     ranged_weapon: WeaponBase = None, ranged_unmount=True, ranged_keep_distance=8, path_distance=True,
                     drop_trash_items=True, trash_items=None, creature_types=None, notorieties=None):
        output = False
        notorieties = [constants.Notoriety.Murderer] if notorieties is None else notorieties
        action_broke = False
        while self.player.alive and (creatures := self._find_mobs(
                mob_find_distance=mob_find_distance, notorieties=notorieties, creature_types=creature_types,
                path_distance=path_distance)):
            for creature in creatures:
                # noinspection PyProtectedMember
                mob = Mob.instantiate(creature.id_, omit_cache=True, force_class=True)
                if mob in self._processed_mobs:
                    if mob.name:
                        log.debug(f"Skipping processed {mob}")
                    continue

                if not mob.name:
                    log.debug(f"Skipping mob without a name {mob}")
                    self._processed_mobs.append(mob)
                    continue

                # noinspection PyProtectedMember
                if mob.type_id is None or mob.id_ == self.player._mount:
                    self._processed_mobs.append(mob)
                    continue

                if mob.dead:
                    log.debug(f"Skipping dead {mob}")
                    self._processed_mobs.append(mob)
                    continue

                # notify = (notify_mutated and mob.mutated) or (
                #             notify_ranged and mob.type_id in constants.TYPE_IDS_MOB_RANGED)
                mob_path_distance = mob.path_distance()
                mob_distance = mob.distance
                # if notify:
                #     tools.telegram_message(f"{mob} detected at distance {mob.path_distance()}",
                #                            disable_notification=not mob.mutated)
                if engage:
                    if not action_broke:
                        self.player.break_action()
                        action_broke = True

                    # noinspection PyProtectedMember
                    max_distance = constants.ENGAGE_MAX_DISTANCE
                    if not ranged and mob_path_distance <= 1:
                        log.debug(f"Already at {mob} at distance path {mob_path_distance}")
                    elif mob_distance > max_distance and mob_path_distance > max_distance:
                        msg = f"Won't engage {mob}. Distance path: {mob_path_distance}, max distance: {max_distance}"
                        log.debug(msg)
                        # tools.telegram_message(msg)
                    else:
                        if drop_overweight_items:
                            self.drop_overweight_items(drop_overweight_items)
                        self.engage_mob(mob, check_health_func=check_health_func, loot=loot, cut=cut,
                                        drop_trash_items=drop_trash_items, notify_only_mutated=notify_mutated,
                                        trash_items=trash_items, ranged=ranged, ranged_weapon=ranged_weapon,
                                        ranged_unmount=ranged_unmount, ranged_keep_distance=ranged_keep_distance)
                        # if notify:
                        #     dead = mob.dead
                        #     tools.telegram_message(f"Done engaging {mob}. Dead: {dead}", disable_notification=dead)
                        output = True
        return output

    @alive_action
    def rearm_from_container(self, weapon_type_ids=None, shield_type_ids=None, container_id=None):
        if self.player.weapon_equipped:
            return

        container_id = container_id or self.loot_container
        container = Container.instantiate(container_id, force_class=True)
        if not container.exists or not container.is_container:
            return

        log.info(f"Rearming from {container}")
        arms = []
        weapon_type_ids = weapon_type_ids or constants.TYPE_IDS_MELEE_WEAPONS
        if weapon_type_ids:
            arms.append(weapon_type_ids)

        shield_type_ids = shield_type_ids or constants.TYPE_IDS_SHIELDS
        if shield_type_ids:
            arms.append(shield_type_ids)

        for arm_type in arms:
            for type_id in arm_type:
                # if self.player.weapon_equipped:
                #     break

                found_weapon = self.player.find_types_container(type_id, container_ids=container, recursive=True)
                if not found_weapon:
                    continue

                found_weapon = random.choice(found_weapon)
                self.player.equip_object(found_weapon, stealth.RhandLayer())
                tools.result_delay()
                break

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

        # todo: yes, this should really repend on the running distance...
        return self.player.near_max_weight is False and self.player.stamina >= self.player.max_stamina * 0.2

    def drink_trash_potions(self):
        trash_potions_type_id = constants.TYPE_IDS_POTIONS_TRASH
        while trash_potions := self.player.find_types_character(trash_potions_type_id):
            for potion in trash_potions:
                potion_object = Item.instantiate(potion)
                log.info(f"Drinking trash potion {potion_object}")
                # noinspection PyProtectedMember
                self.player._use_object(potion_object)
                tools.delay(constants.POTION_COOLDOWN)
