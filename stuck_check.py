import pendulum

from entities.base_scenario import ScenarioBase, log, stealth, tools, constants
from entities.script import get_running_scripts

DEBUG = False
STUCK_IF_DEAD = False


class StuckCheck(ScenarioBase):
    def __init__(self):
        super().__init__()
        self._journal_len = 0
        self.stuck_timeout_seconds = None

    def start(self, stuck_timeout=None, **kwargs):
        if DEBUG:
            tools.debug(port=12346)
        # self.script.rename(self.name)  # todo: rename to __init__ and move to base after fix
        # super(type(self), self).start(**kwargs)  # this is not needed
        if (stuck_timeout := stuck_timeout or stealth.GetGlobal('char', constants.VAR_STUCK_TIMEOUT)) is not None:
            self.stuck_timeout_seconds = int(stuck_timeout)
            log.info(f"Starting {self} with timeout {self.stuck_timeout_seconds} seconds")
            self.stuck_check_loop()

    def stuck_check_loop(self):
        stealth.SetPauseScriptOnDisconnectStatus(False)
        stealth.SetARStatus(True)
        stealth.SetGlobal('char', constants.VAR_RECONNECTS, 0)
        self.player.last_move = pendulum.now()
        self._journal_len = stealth.HighJournal()
        while True:
            running_scripts = get_running_scripts()
            if len(running_scripts) == 1:
                msg = f"{self.player}: {self} is alone. Stopping"
                log.info(msg)
                tools.telegram_message(msg)
                self.script.stop()
                break

            if stealth.Connected():
                paused_scripts = [i for i in running_scripts if i.paused]
                if paused_scripts:
                    log.info(f"{self} is connected. Unpausing all scripts")
                    tools.delay(2000)
                    self.script.unpause_all_except_this()
                # paused_scripts = [i for i in running_scripts if i.paused]
                # if paused_scripts:
                #     log.info(f"Waiting for paused scripts: {paused_scripts}")
                # else:
                self.stuck_check()
            else:
                self.script.pause_all_except_this()
            tools.delay(1000)

        log.info(f"{self} stopped.")

    def stuck_check(self):
        if self.stuck_timeout_seconds is None:
            return

        if not STUCK_IF_DEAD and self.player.dead:
            log.debug(f"{self} is dead. Skipping stuck check")
            tools.delay(10000)
            return

        stuck = False
        last_move = self.player.last_move
        # log.info(f"{self} stuck_check: last_move: {last_move}")
        stuck_timer = pendulum.now() - last_move
        stuck_timer_seconds = stuck_timer.in_seconds()
        if stuck_timer_seconds > self.stuck_timeout_seconds * 0.75:
            log.info(f"❗{self} stuck_timer: {stuck_timer_seconds}/{self.stuck_timeout_seconds}")
        elif stuck_timer_seconds == 0:
            self._journal_len = stealth.HighJournal()
        elif stuck_timer_seconds > 0 and stuck_timer_seconds % int(self.stuck_timeout_seconds / 10) == 0:
            log.info(f"{self} stuck_timer: {stuck_timer_seconds}/{self.stuck_timeout_seconds}")
            if stuck_timer_seconds > 15:
                if self._journal_len == stealth.HighJournal():
                    log.info(f"{self}: Journal not updated. Considering stuck.")
                    stuck = True

        if not stuck and (not self.player.connected or not self.player.is_stuck(self.stuck_timeout_seconds)):
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
            stealth.SetARStatus(True)
            tools.reconnect()
            self.player.last_move = pendulum.now()


if __name__ == '__main__':
    log.verbose = True
    StuckCheck().start()
    print("")
