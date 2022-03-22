from entities.base_script import ScriptBase, log, stealth, tools, constants


class Template(ScriptBase):
    def __init__(self):
        super().__init__()

    def start(self):
        super(type(self), self).start()


if __name__ == '__main__':
    Template().start()
    print("")
