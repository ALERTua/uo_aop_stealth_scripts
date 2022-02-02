from entities.player import Player
from tools import tools
import py_stealth as stealth
from tools.tools import log

player = Player()


def main():
    log.info('Start')
    old_bowcraft = stealth.GetSkillValue('bowcraft')
    while (bowcraft := stealth.GetSkillValue('bowcraft')) < 90.0:
        if old_bowcraft != bowcraft:
            log.info(f"Bowcraft changed to {bowcraft}")
        old_bowcraft = bowcraft
        tools._delay(60000)
    log.info(f'Done. Bowcraft is now {bowcraft}')
    stealth.SetARStatus(False)
    stealth.Disconnect()
    stealth.CorrectDisconnection()
    exit()


if __name__ == '__main__':
    main()
