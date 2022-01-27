import signal
import atexit
import pendulum
import pprint

from tools import constants, tools
from .mob import Mob
from .player import Player, alive_action
from py_stealth import *

log = AddToSystemJournal


class ScriptBase:
    def __init__(self):
        self.player = Player()
        self._start_time = None
        self._processed_mobs = []
        self.script_stats = {}
        self._register_signals()
        self.commands_cooldown_sec = 30
        self._commands_cooldown = {}
        atexit.register(self.at_exit)

    def _register_signals(self):
        signals = (signal.SIGABRT, signal.SIGBREAK, signal.SIGFPE, signal.SIGILL, signal.SIGINT, signal.SIGSEGV,
                   signal.SIGTERM)
        for signal_ in signals:
            signal.signal(signal_, self.at_exit)

    def at_exit(self):
        log(f"{self} atexit. Script stats:\n{self.script_stats_str}")

    def __str__(self):
        return self.name

    def stop(self):
        log(f"Stopping {self}")
        self.at_exit()
        StopAllScripts()

    def _parse_command(self, command):
        return tools.in_journal(f'{self.player.name}: {command}') and not self._commmand_on_cooldown(command)

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
        if self.script_stats:
            return log(f"{self} stats:\n{self.script_stats_str}")

    def parse_commands(self):
        if self._parse_command('quit'):
            self._command_add_cooldown('quit')
            return self.quit()
        elif self._parse_command('stop'):
            self._command_add_cooldown('stop')
            return self.stop()
        elif self._parse_command('stats'):
            self._command_add_cooldown('stats')
            return self.report_stats()

    @property
    def script_stats_str(self):
        return pprint.pformat(self.script_stats, indent=2, width=10)

    @property
    def name(self):
        return self.__class__.__name__

    @alive_action
    def wait_stamina(self, threshold=20):
        if self.player.stamina < threshold:
            log(f"Waiting stamina at least {threshold}")
        else:
            return

        while self.player.alive and self.player.stamina < threshold:
            tools.ping_delay()
        log(f"Stamina reached {threshold}")

    @alive_action
    def _pick_up_items(self, type_ids):
        for type_id in type_ids:
            while (loot := self.player.find_type_ground(type_id, constants.MAX_PICK_UP_DISTANCE)) \
                    and not self.player.loot_ground(loot):
                log(f"Looting {loot}")
                tools.ping_delay()

    @alive_action
    def engage_mob(self, mob: Mob, check_health_func=None, loot=True, cut=True, drop_trash_items=True,
                   notify_only_mutated=True):
        check_health_func = check_health_func or self.check_health
        log(f"Engaging {mob} distance {mob.path_distance()}")
        while mob.alive:
            self.player.move(mob.x, mob.y)
            self.player.attack(mob.id_)
            check_health_func()  # script_check_health in scripts
        log(f"Done Engaging {mob}")
        if not notify_only_mutated or (notify_only_mutated and mob.mutated):
            tools.telegram_message(f"{mob} dead", disable_notification=not mob.mutated)
        if loot:
            self.player.loot_nearest_corpse(cut_corpse=cut, drop_trash_items=drop_trash_items)

    def drop_trash(self):
        return self.player.drop_trash_items(constants.ITEM_IDS_MINING_TRASH)

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

                drop_object_name = GetName(drop_object_id)
                drop_object_quantity = GetQuantity(drop_object_id)
                if not drop_object_quantity:
                    break

                drop_quantity = min((weight_drop_needed // drop_weight) + 1, drop_object_quantity)
                log(f"Need to relieve of {weight_drop_needed}st. Dropping {drop_quantity}x{drop_weight}st "
                    f"of {drop_object_name}{drop_object_id}")
                drop_result = self.player.drop_item(drop_object_id, drop_quantity)
                tools.result_delay()
                new_item_id = self.player.find_type_backpack(drop_type, drop_color)
                if drop_result or (new_item_id != drop_object_id or drop_object_quantity != GetQuantity(new_item_id)):
                    log(f"Drop successful")
                    break

    def quit(self):
        log("Quitting")
        self.at_exit()
        self.disconnect()
        exit()

    @staticmethod
    def disconnect():
        SetARStatus(False)
        Disconnect()
        CorrectDisconnection()

    @property
    def script_running_time(self):
        script_running_time = pendulum.now() - self._start_time
        return script_running_time

    @property
    def script_running_time_words(self):
        return self.script_running_time.in_words()

    def check_health(self):
        if self.player.dead:
            tools.telegram_message(f'{self.player} is dead. Script ran for {self.script_running_time_words}')
            self.player.move(*constants.COORDS_MINOC_HEALER)
            self.quit()
        need_heal = (self.player.max_hp - self.player.hp) > (self.player.max_hp * 0.4)
        if need_heal:
            if self.player.got_bandages:
                self.player.bandage_self_if_hurt()
                return True
            else:
                return False
        else:
            return True

    @alive_action
    def got_bandages(self, quantity):
        return GetQuantity(self.player.find_type_backpack(constants.TYPE_ID_BANDAGE)) == quantity

    @alive_action
    def _check_bandages(self, quantity, container_id):
        log("Checking Bandages")
        player_bandages = self.player.got_bandages
        if not player_bandages or GetQuantity(player_bandages) < quantity:
            bandages = FindType(constants.TYPE_ID_BANDAGE, container_id)
            if not bandages:
                log("WARNING! NO SPARE BANDAGES FOUND!")
                tools.telegram_message(f"{self.player}: No bandages found. "
                                       f"Script ran for {self.script_running_time_words}")
                self.quit()
                return

            while not self.got_bandages(quantity) and not self.player.move_item(bandages, quantity):
                log("Grabbing Bandages")
                tools.ping_delay()

    @alive_action
    def _eat(self, container_id, food_type=None):
        food_type = food_type or constants.TYPE_ID_FOOD_FISHSTEAKS
        log("Eating")
        food = FindType(food_type, container_id)
        if not food:
            log("WARNING! NO FOOD FOUND!")
            tools.telegram_message(f"{self.player}: No food found", disable_notification=True)
            return

        self.player.use_object(food)

    @alive_action
    def process_mobs(self, mob_type_ids, engage=True, notify_only_mutated=True):
        for mob_type_id in mob_type_ids:
            mob_id = self.player.find_type_ground(mob_type_id, constants.AGGRO_RANGE)
            if mob_id and mob_id not in self._processed_mobs:
                mob = Mob(mob_id)
                self._processed_mobs.append(mob_id)
                if not notify_only_mutated or (notify_only_mutated and mob.mutated):
                    tools.telegram_message(f"Mob {mob} detected at distance {mob.distance}",
                                           disable_notification=not mob.mutated)
                if engage:
                    mob_distance = mob.path_distance()
                    max_distance = constants.ENGAGE_MAX_DISTANCE
                    if mob_distance > max_distance:
                        log(f"Won't engage {mob}. Distance path: {mob_distance} > {max_distance}")
                    else:
                        self.engage_mob(mob)

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
        return self.player.near_max_weight is False and self.player.stamina > 10
