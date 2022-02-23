from entities.base_script import ScriptBase, log, stealth, tools, constants


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
            stealth.WaitTargetSelf()
            stealth.UseSkill(skill_name)
            tools.delay(constants.SKILL_COOLDOWN)


if __name__ == '__main__':
    EvaluatingInteligence().start()
    print("")
