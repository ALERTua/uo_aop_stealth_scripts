from entities.base_script import ScriptBase, log, stealth, tools, constants


class Hiding_Stealth(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        super(type(self), self).start()
        while True:
            stealth_skill_name = 'stealth'
            stealth_value = stealth.GetSkillValue(stealth_skill_name)
            if stealth_value == 100.0:
                self.quit(f'{self.player.name} {stealth_skill_name} reached {stealth_value}')

            while True:
                self.player.hide_until_hidden()
                while self.player.hidden:
                    stealth.UseSkill(stealth_skill_name)
                    tools.delay(constants.SKILL_COOLDOWN)


if __name__ == '__main__':
    Hiding_Stealth().start()
    print("")
