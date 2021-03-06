from entities.base_scenario import ScenarioBase, log, stealth, tools, constants

LASTOBJECT_LASTTARGET = False
LASTOBJECT = 0x728EF888
LASTTARGET = 0x728B10FA


class Inscription(ScenarioBase):
    def __init__(self):
        super().__init__()

    def start(self):
        super(type(self), self).start()
        skill_name = 'Inscription'
        while True:
            if stealth.GetSkillValue(skill_name) == 100.0:
                self.disconnect()

            scepter = self.player.find_type_backpack(constants.TYPE_ID_SCEPTER)
            if not scepter:
                self.player.open_container(self.player.backpack, subcontainers=True)
                self.player.open_container(self.player.backpack, subcontainers=True)
                tools.delay(1000)
                scepter = self.player.find_type_backpack(constants.TYPE_ID_SCEPTER, recursive=True)
                if not scepter:
                    log.error("No scepters found. Cannot proceed")
                    self.quit()

            mana_threshold = self.player.max_mana * 0.95
            if stealth.GetSkillValue('meditation') == 100.0:
                meditation_trigger = 50
            else:
                meditation_trigger = mana_threshold

            if self.player.mana < meditation_trigger:
                log.info('Meditating')
                stealth.UseSkill('meditation')
                i = 0
                while self.player.mana < mana_threshold:
                    if stealth.GetSkillValue('meditation') < 100.0:
                        if i > 0:
                            stealth.UseSkill('meditation')
                        self.player.break_action()
                    i += 1
                    tools.delay(constants.SKILL_COOLDOWN)

            log.info('Inscripting')
            stealth.CancelWaitTarget()
            stealth.WaitTargetObject(scepter)
            stealth.UseSkill(skill_name)
            if stealth.GetSkillValue(skill_name) >= 80.0:
                stealth.WaitMenu('Choose a Circle', 'Seventh Circle')
                stealth.WaitMenu('Choose the Spell', 'Gate Travel')
            elif stealth.GetSkillValue(skill_name) >= 65.0:
                stealth.WaitMenu('Choose a Circle', 'Sixth Circle')
                stealth.WaitMenu('Choose the Spell', 'Energy Bolt')
            elif stealth.GetSkillValue(skill_name) >= 25.0:
                stealth.WaitMenu('Choose a Circle', 'Third Circle')
                stealth.WaitMenu('Choose the Spell', 'Poison')
            else:
                stealth.WaitMenu('Choose a Circle', 'First Circle')
                stealth.WaitMenu('Choose the Spell', 'Magic Arrow')

            if LASTOBJECT_LASTTARGET:
                tools.delay(200)
                stealth.UseObject(LASTOBJECT)
                stealth.CancelWaitTarget()
                stealth.WaitTargetObject(LASTTARGET)
            tools.delay(constants.SKILL_COOLDOWN)


if __name__ == '__main__':
    Inscription().start()
    print("")
