import pendulum

from entities.base_scenario import ScenarioBase, log, stealth, tools, constants
from entities.script import get_running_scripts


class StuckCheck(ScenarioBase):
    def __init__(self):
        super().__init__()
        self.stuck_timeout_seconds = None

    def start(self, stuck_timeout=None, **kwargs):
        # super(type(self), self).start(**kwargs)  # this is not needed
        if (stuck_timeout := stuck_timeout or stealth.GetGlobal('char', 'stuck_timeout')) is not None:
            self.stuck_timeout_seconds = int(stuck_timeout)
            log.info(f"Starting {self} with timeout {self.stuck_timeout_seconds} seconds")
            self.stuck_check_loop()

    def stuck_check_loop(self):
        while True:
            running_scripts = get_running_scripts()
            if len(running_scripts) == 1:
                log.info(f"{self} stuck_check_loop: {running_scripts}. breaking")
                break

            paused_scripts = [i for i in running_scripts if i.paused]
            if len(paused_scripts) > 0:
                log.info(f"{self} is paused. Waiting for {paused_scripts} to unpause...")
            else:
                self.stuck_check()
            tools.delay(1000)

        log.info(f"{self} stopped.")

    def stuck_check(self, **kwargs):
        if self.stuck_timeout_seconds is None:
            return

        last_move = self.player.last_move
        # log.info(f"{self} stuck_check: last_move: {last_move}")
        stuck_timer = pendulum.now() - last_move
        if stuck_timer.in_seconds() > self.stuck_timeout_seconds * 0.75:
            log.info(f"❗{self} stuck_timer: {stuck_timer.in_seconds()}/{self.stuck_timeout_seconds}")

        if not self.player.connected or not self.player.is_stuck(self.stuck_timeout_seconds):
            return

        if stealth.GetGlobal('char', 'reconnected'):
            msg = f"⛔{self.player} stuck for {self.stuck_timeout_seconds} seconds. Stopping {self.name}."
            log.error(msg)
            self.quit(message=msg, alarm=True)
            stealth.SetARStatus(False)
            stealth.CorrectDisconnection()
            stealth.StopAllScripts()
        else:
            log.info("⛔Stuck. Reconnecting...")
            stealth.SetGlobal('char', 'reconnected', 'true')
            # stealth.SetARStatus(True)
            stealth.Disconnect()
            tools.delay(5000)
            self.player.last_move = pendulum.now()


if __name__ == '__main__':
    log.verbose = True
    StuckCheck().start()
    print("")