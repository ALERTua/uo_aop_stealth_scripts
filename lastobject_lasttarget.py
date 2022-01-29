from entities.base_script import ScriptBase, log, stealth
from tools import tools

debug = False


class LastObjectLastTarget(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        last_object = self.player.last_object
        last_target = self.player.last_target
        while last_object.exists and last_target.exists:
            self.player.use_object(last_object)
            stealth.WaitTargetObject(last_target)
        self.quit()


if __name__ == '__main__':
    if debug:
        tools.debug()
    LastObjectLastTarget().start()
    print("")
