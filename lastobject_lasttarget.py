from entities.base_script import ScriptBase, stealth
from tools import tools
from tools.tools import log


class LastObjectLastTarget(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        super(type(self), self).start()
        last_object = self.player.last_object
        last_target = self.player.last_target
        while last_object.exists and last_target.exists:
            self.player.use_object(last_object)
            stealth.WaitTargetObject(last_target)
        self.quit()


if __name__ == '__main__':
    LastObjectLastTarget().start()
    print("")
