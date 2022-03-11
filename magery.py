from entities.base_script import ScriptBase, log, stealth, tools, constants

LASTOBJECT_LASTTARGET = False
LASTOBJECT = 0x72FD39D6
LASTTARGET = 0x73150FC1


class Magery(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        super(type(self), self).start()
        HEALTH_THRESHOLD = self.player.max_hp * 0.5
        while True:
            if self.player.mana < self.player.max_mana - 10:
                log.debug('Meditating')
                stealth.UseSkill('meditation')
                self.player.break_action()
                # tools.delay(constants.SKILL_COOLDOWN)

            elif self.player.hp > HEALTH_THRESHOLD and self.player.mana > 10:
                log.debug('Casting')
                stealth.CancelWaitTarget()
                stealth.WaitTargetSelf()
                # if stealth.GetSkillValue('magery') > 25:
                stealth.Cast('Poison')
                # else:
                #     stealth.Cast('Magic Arrow')

            if (stealth.GetSkillValue('healing') > 70 and self.player.poisoned) \
                    or self.player.hp < HEALTH_THRESHOLD:
                log.debug('Healing')
                self.player._bandage_self()
            elif LASTOBJECT_LASTTARGET:
                log.debug('LastObject-LastTarget')
                tools.delay(200)
                stealth.UseObject(LASTOBJECT)
                stealth.CancelWaitTarget()
                stealth.WaitTargetObject(LASTTARGET)

            tools.delay(constants.SKILL_COOLDOWN)


if __name__ == '__main__':
    Magery().start()
    print("")
