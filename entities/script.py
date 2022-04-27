import pendulum
import stealth
from pathlib import Path
from tools import constants, tools
from tools.tools import log
from typing import List


class Script:
    def __init__(self, path, direct=True):
        if direct:
            raise Exception(f"Direct instantiation of {self.__class__.__name__} is not supported")

        self.path = Path(path)
        self.name = path.stem.capitalize()

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.path == other.path

    @classmethod
    def instantiate(cls, path_or_name):
        path = Path(path_or_name)
        if not path.is_file() or not path.exists():
            path = Path(__file__).parent.parent / path
            if not path.is_file() or not path.exists():
                path = path.with_suffix('.py')
                assert path.is_file() and path.exists(), f"{path} is not a valid script"

        return cls(path, direct=False)

    @property
    def index(self):
        output = get_running_scripts().index(self)
        assert Path(stealth.GetScriptPath(output)) == self.path, "got wrong index"
        return output

    @property
    def running(self):
        return self in get_running_scripts()

    @property
    def paused(self):
        return not bool(int(stealth.GetScriptState(self.index)))

    def start(self):
        if not self.running:
            stealth.StartScript(str(self.path))

    def stop(self):
        if self.running:
            stealth.StopScript(str(self.path))


def get_running_scripts() -> List[Script]:
    output = []
    for i in range(stealth.GetScriptCount()):
        output.append(Script.instantiate(stealth.GetScriptPath(i)))

    return output
