from entities.base_scenario import ScenarioBase, log, stealth, tools, constants

LASTOBJECT_LASTTARGET = False
LASTOBJECT = 0x728EF888
LASTTARGET = 0x7356EF50


class Hiding_Stealth(ScenarioBase):
    def __init__(self):
        super().__init__()

    def lo_lt(self):
        if LASTOBJECT_LASTTARGET:
            object_ = stealth.LastObject() if LASTOBJECT is True else LASTOBJECT
            target = stealth.LastTarget() if LASTTARGET is True else LASTTARGET
            if object_ and target:
                stealth.CancelWaitTarget()
                stealth.UseObject(object_)
                stealth.WaitTargetObject(target)

    def start(self):
        super(type(self), self).start()
        stealth_skill_name = 'stealth'
        hiding_skill_name = 'hiding'

        def hide():
            log.debug(hiding_skill_name)
            stealth.UseSkill(hiding_skill_name)
            self.lo_lt()
            tools.delay(constants.SKILL_COOLDOWN)

        while True:
            stealth_value = stealth.GetSkillValue(stealth_skill_name)
            hiding_value = stealth.GetSkillValue(hiding_skill_name)
            if stealth_value == 100 and hiding_value == 100:
                self.quit(f'{self.player.name} {hiding_skill_name} reached {hiding_value} & '
                          f'{stealth_skill_name} reached {stealth_value}')

            while not self.player.hidden:
                hide()

            if hiding_value >= 90 and stealth_value < 100:
                log.debug(f'Stealthing with level {stealth_value}')
                stealth.UseSkill(stealth_skill_name)
                self.lo_lt()
                tools.delay(constants.SKILL_COOLDOWN)
            else:
                hide()


if __name__ == '__main__':
    Hiding_Stealth().start()
    print("")
