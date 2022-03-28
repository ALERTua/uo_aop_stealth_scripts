from entities.base_script import ScriptBase, log, stealth, tools, constants

LASTOBJECT_LASTTARGET = True
LASTOBJECT = 0x728EF888
LASTTARGET = 0x7356EF50


class Hiding_Stealth(ScriptBase):
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
        while (stealth_value := stealth.GetSkillValue(stealth_skill_name)) < 100:
            while not self.player.hidden:
                self.player.hide()
                self.lo_lt()

            if stealth.GetSkillValue('hiding') >= 90:
                log.debug(f'Stealthing with level {stealth_value}')
                stealth.UseSkill(stealth_skill_name)
                self.lo_lt()
                tools.delay(constants.SKILL_COOLDOWN)
            else:
                self.player.hide()
                self.lo_lt()

        self.quit(f'{self.player.name} {stealth_skill_name} reached {stealth_value}')


if __name__ == '__main__':
    Hiding_Stealth().start()
    print("")
