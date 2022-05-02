import pendulum

from entities.base_scenario import ScenarioBase, log, stealth, tools, constants
from entities.script import get_running_scripts


class StuckCheck(ScenarioBase):
    def __init__(self):
        super().__init__()
        self.stuck_timeout_seconds = None

    def start(self, stuck_timeout=None, **kwargs):
        # super(type(self), self).start(**kwargs)  # this is not needed
        if (stuck_timeout := stuck_timeout or stealth.GetGlobal('char', constants.VAR_STUCK_TIMEOUT)) is not None:
            self.stuck_timeout_seconds = int(stuck_timeout)
            log.info(f"Starting {self} with timeout {self.stuck_timeout_seconds} seconds")
            self.stuck_check_loop()

    def stuck_check_loop(self):
        stealth.SetPauseScriptOnDisconnectStatus(False)
        while True:
            running_scripts = get_running_scripts()
            if len(running_scripts) == 1:
                log.info(f"{self} is alone. Stopping")
                self.script.stop()
                break

            if stealth.Connected():
                # log.info(f"{self} is connected. Unpausing all scripts")
                # self.script.unpause_all_except_this()
                paused_scripts = [i for i in running_scripts if i.paused]
                if paused_scripts:
                    log.info(f"Waiting for paused scripts: {paused_scripts}")
            else:
                self.script.pause_all_except_this()
            tools.delay(1000)

        log.info(f"{self} stopped.")

    def stuck_check(self, **kwargs):
        if self.stuck_timeout_seconds is None:
            return

        last_move = self.player.last_move
        # log.info(f"{self} stuck_check: last_move: {last_move}")
        stuck_timer = pendulum.now() - last_move
        stuck_timer_seconds = stuck_timer.in_seconds()
        if stuck_timer_seconds > self.stuck_timeout_seconds * 0.75:
            log.info(f"❗{self} stuck_timer: {stuck_timer_seconds}/{self.stuck_timeout_seconds}")

        if not self.player.connected or not self.player.is_stuck(self.stuck_timeout_seconds):
            return

        reconnects = int(stealth.GetGlobal('char', constants.VAR_RECONNECTS) or 0)
        reconnects_limit = int(stealth.GetGlobal('char', constants.VAR_RECONNECTS_LIMIT) or 2)
        if reconnects > reconnects_limit:
            msg = f"⛔{self.player} stuck {reconnects} times for {stuck_timer_seconds}/{self.stuck_timeout_seconds} " \
                  f"seconds. Stopping {self.name}."
            log.error(msg)
            self.script.stop_all_except_this()
            self.quit(message=msg, alarm=True)
            stealth.SetARStatus(False)
            stealth.CorrectDisconnection()
        else:
            log.info("⛔Stuck. Reconnecting...")
            new_reconnects = reconnects + 1
            tools.telegram_message(f'{self.player} reconnecting {self.name} {new_reconnects}/{reconnects_limit}: '
                                   f'{stuck_timer_seconds}/{self.stuck_timeout_seconds}', disable_notification=True)
            stealth.SetGlobal('char', constants.VAR_RECONNECTS, new_reconnects)
            # stealth.SetARStatus(True)
            stealth.Disconnect()
            tools.delay(5000)
            self.player.last_move = pendulum.now()


if __name__ == '__main__':
    log.verbose = True
    StuckCheck().start()
    print("")
