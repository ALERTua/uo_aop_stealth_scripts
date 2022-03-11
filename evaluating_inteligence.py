from entities.base_script import ScriptBase, log, stealth, tools, constants

LASTOBJECT_LASTTARGET = True
LASTOBJECT = 0x728EF888
LASTTARGET = 0x728B10FA


class EvaluatingInteligence(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        super(type(self), self).start()
        skill_name = 'Evaluate Intelligence'
        while True:
            if stealth.GetSkillValue(skill_name) == 100.0:
                self.disconnect()

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
