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
        running_scripts = get_running_scripts()
        this_script = [i for i in running_scripts if i.path == self.path]
        assert this_script, f"{self} is not running"
        output = running_scripts.index(this_script[0])
        assert Path(stealth.GetScriptPath(output)) == self.path, "got wrong index"
        return output

    @property
    def running(self):
        return self in get_running_scripts()

    @property
    def state(self):
        return int(stealth.GetScriptState(self.index))

    @property
    def paused(self):
        return self.state == 2

    def start(self):
        if not self.running:
            log.info(f"Starting {self}")
            stealth.StartScript(str(self.path))

    def stop(self):
        if self.running:
            log.info(f"Stopping {self}")
            stealth.StopScript(self.index)

    def stop_all_except_this(self):
        log.info(f"Stopping all scripts except {self}")
        for script in get_running_scripts():
            if script.path != self.path:
                script.stop()

    def pause_all_except_this(self):
        # log.info(f"Pausing all scripts except {self}")
        for script in get_running_scripts():
            if script.path != self.path:
                script.pause()

    def unpause_all_except_this(self):
        # log.info(f"Unpausing all scripts except {self}")
        for script in get_running_scripts():
            # log.info(f"{script} {script.index} {script.paused} {stealth.GetScriptState(script.index)}")
            if script.path != self.path:
                script.resume()

    def pause(self):
        if not self.paused:
            log.info(f"Pausing {self}")
            stealth.PauseResumeScript(self.index)

    def resume(self):
        if self.paused:
            log.info(f"Resuming {self}")
            stealth.PauseResumeScript(self.index)

    def restart(self):
        log.info(f"Restarting {self}")
        self.stop()
        self.start()

    def restart_all_except_this(self):
        log.info(f"Restarting all scripts except {self}")
        for script in get_running_scripts():
            if script != self:
                script.restart()

    def rename(self, name):
        stealth.SetScriptName(self.index, name)


def get_running_scripts() -> List[Script]:
    output = []
    scripts_count = stealth.GetScriptCount()
    for i in range(scripts_count):
        script_path = stealth.GetScriptPath(i)
        script = Script.instantiate(script_path)
        output.append(script)

    return output
