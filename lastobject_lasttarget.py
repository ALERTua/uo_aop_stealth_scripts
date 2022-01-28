from tools import tools
from entities.base_script import ScriptBase
from py_stealth import *

log = AddToSystemJournal

debug = False


class LastObjectLastTarget(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        last_object = self.player.last_object
        last_target = self.player.last_target
        while last_object.exists and last_target.exists:
            self.player.use_object(last_object)
            WaitTargetObject(last_target)
        self.quit()


if __name__ == '__main__':
    if debug:
        tools.debug()
    LastObjectLastTarget().start()
    print("")
