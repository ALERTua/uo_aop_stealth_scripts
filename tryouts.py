from entities.player import Player
from tools import tools
import py_stealth as stealth
from tools.tools import log

player = Player()


def wait_for_skill_level(skill_name, level):
    log.info('Start')
    old_skill = stealth.GetSkillValue(skill_name)
    log.info(f"Initing with {old_skill}")
    while (skill := stealth.GetSkillValue(skill_name)) < level:
        if old_skill != skill:
            log.info(f"Skill changed to {skill}")
        old_skill = skill
        tools.delay(60000)
    log.info(f'Done. Skill is now {skill}')
    stealth.SetARStatus(False)
    stealth.Disconnect()
    stealth.CorrectDisconnection()
    exit()


def main():
    wait_for_skill_level('carpentry', 60)


if __name__ == '__main__':
    main()
