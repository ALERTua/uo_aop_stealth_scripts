from entities.base_scenario import ScenarioBase, log, stealth, tools, constants


class Template(ScenarioBase):
    def __init__(self):
        super().__init__()

    def start(self, **kwargs):
        super(type(self), self).start(**kwargs)


if __name__ == '__main__':
    Template().start()
    print("")
