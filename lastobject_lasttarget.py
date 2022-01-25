from tools import tools
from entities.base_script import ScriptBase
from py_stealth import *

log = AddToSystemJournal

debug = False


class LastObjectLastTarget(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        while True:
            self.player.use_object(LastObject())
            WaitTargetObject(LastTarget())


if __name__ == '__main__':
    if debug:
        tools.debug()
    LastObjectLastTarget().start()
    print("")
