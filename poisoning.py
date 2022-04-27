from entities.base_scenario import ScenarioBase, log, stealth, tools, constants
import pendulum

from entities.item import Item


class Poisoning(ScenarioBase):
    def __init__(self):
        super().__init__()

    @property
    def mortar_pestal(self):
        output = self.player.find_type(constants.TYPE_ID_TOOL_MORTAR_PESTAL)
        if not output:
            msg = f"Couldn't find mortar and pestal. Quitting"
            log.error(msg)
            tools.telegram_message(msg)
            self.quit()

        output = Item.instantiate(output)
        return output

    def craft_poison_bottle(self):
        mortar_pestal = self.mortar_pestal
        if not mortar_pestal:
            log.error(f"Cannot craft poison bottle. No Mortar and Pestal")
            return

        nightshade = stealth.NSCount()
        if not nightshade:
            log.error(f"Cannot craft poison bottle. No Nightshade found")
            return

        empty_bottle = self.player.find_types_backpack(constants.TYPE_ID_EMPTY_BOTTLE, recursive=False)
        if not empty_bottle:
            log.error(f"Cannot craft poison bottle. No Empty Bottles")
            return

        empty_bottle = empty_bottle[0]

        log.info(f"Crafting poison bottle using {mortar_pestal} and {empty_bottle}")
        stealth.CancelAllMenuHooks()
        stealth.CloseMenu()
        stealth.CancelWaitTarget()
        stealth.WaitTargetObject(empty_bottle.id_)
        stealth.UseObject(mortar_pestal.id_)
        stealth.WaitMenu('Alchemy', 'Poison Potions')
        stealth.WaitMenu('Poison Potions', 'Deadly poison potion 95% Alchemy')

    @property
    def poison_bottle(self):
        while not (poison_bottle := self.player.find_types_backpack(constants.TYPE_ID_POTION_POISON, recursive=True)):
            self.craft_poison_bottle()
            tools.delay(constants.POTION_COOLDOWN)
        return poison_bottle[0]

    def poison_item(self, item_id):
        poison_bottle = self.poison_bottle
        if not poison_bottle:
            log.error(f"Cannot poison. No poison bottles")
            return

        poison_bottle = Item.instantiate(poison_bottle)
        item = Item.instantiate(item_id)
        log.info(f"Poisoning {item} with {poison_bottle}")
        while True:
            stealth.CancelWaitTarget()
            stealth.CancelTarget()
            stealth.WaitTargetObject(poison_bottle.id_)
            stealth.UseSkill('poisoning')
            tools.result_delay()
            journal_start = stealth.HighJournal()
            stealth.WaitTargetObject(item.id_)
            tools.result_delay()
            journal_contents = tools.journal(journal_start)
            fail = [j for j in journal_contents if j.contains('You fail to apply the poison.')]
            tools.delay(constants.SKILL_COOLDOWN)
            if not fail:
                break

            log.debug(f"{item} poisoning attempt failed. Trying again")

        item.poisoned = True
        log.info(f"{item} successfuly poisoned")

    def start(self):
        super(type(self), self).start()
        self.player.open_container(self.player.backpack, subcontainers=True)
        unprocessed_items = self.player.find_types_backpack(constants.TYPE_IDS_MELEE_WEAPONS, recursive=True)
        while unprocessed_items:
            unprocessed_item = unprocessed_items.pop(0)
            item = Item.instantiate(unprocessed_item)
            item_poisoned = item.poisoned
            if item_poisoned:
                log.info(f"{item} is already poisoned")
                continue

            self.poison_item(item)
            log.info(f"{len(unprocessed_items)} unprocessed items left")
            tools.delay(constants.SKILL_COOLDOWN)

        log.info(f"Done")


if __name__ == '__main__':
    poisoning = Poisoning()
    poisoning.start()
    print("")
