from functools import wraps

import pendulum

import constants
import tools
from player import Player, alive_action
from py_stealth import *

log = AddToSystemJournal


class ScriptBase:
    def __init__(self):
        self.player = Player()
        self._start_time = None
        self._detected_mobs = []

    @alive_action
    def wait_stamina(self, threshold=20):
        if self.player.stamina < threshold:
            log(f"Waiting stamina at least {threshold}")
        else:
            return

        while self.player.alive and self.player.stamina < threshold:
            Wait(1000)
        log(f"Stamina reached {threshold}")

    @alive_action
    def _pick_up_items(self, type_ids):
        for type_id in type_ids:
            loot = self.player.find_type_ground(type_id, 3)
            loot_result = None
            while loot and not loot_result:
                log(f"Looting {loot}")
                loot_result = self.player.loot_ground(loot)
                loot = self.player.find_type_ground(type_id, 3)

    @alive_action
    def _drop_overweight_items(self, drop_types):
        for drop_type, drop_color, drop_weight in drop_types:
            weight_drop_needed = self.player.weight - self.player.max_weight
            if weight_drop_needed < 1:
                break

            while True:
                weight_drop_needed = self.player.weight - self.player.max_weight
                if weight_drop_needed < 1:
                    break

                drop_object_id = self.player.backpack_find_type(drop_type, drop_color)
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
                new_item_id = self.player.backpack_find_type(drop_type, drop_color)
                if drop_result or (new_item_id != drop_object_id or drop_object_quantity != GetQuantity(new_item_id)):
                    log(f"Drop successful")
                    break

    def quit(self):
        log("Quitting")
        self.disconnect()
        exit()

    def disconnect(self):
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
        if (self.player.max_hp - self.player.hp) > 60:
            if self.player.got_bandages:
                self.player.bandage_self_if_hurt()
                return True
            else:
                return False
        else:
            return True

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

            log("Grabbing Bandages")
            self.player.move_item(bandages, 3)
            Wait(500)

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
