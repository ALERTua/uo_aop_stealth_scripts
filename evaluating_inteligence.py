from entities.base_scenario import ScenarioBase, log, stealth, tools, constants

LASTOBJECT_LASTTARGET = True
LASTOBJECT = 0x728EF888
LASTTARGET = 0x728B10FA


class EvaluatingInteligence(ScenarioBase):
    def __init__(self):
        super().__init__()

    def start(self):
        super(type(self), self).start()
        skill_name = 'Evaluate Intelligence'
        while True:
            skill_value = stealth.GetSkillValue(skill_name)
            if skill_value == 100.0:
                self.quit(f'{self.player.name} {skill_name} reached {skill_value}')

            stealth.CancelWaitTarget()
            stealth.UseSkill(skill_name)
            stealth.WaitTargetSelf()
            if LASTOBJECT_LASTTARGET:
                tools.delay(200)
                stealth.UseObject(LASTOBJECT)
                stealth.CancelWaitTarget()
                stealth.WaitTargetObject(LASTTARGET)
            tools.delay(constants.SKILL_COOLDOWN)


if __name__ == '__main__':
    EvaluatingInteligence().start()
    print("")
