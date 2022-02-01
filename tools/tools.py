import inspect
import os
import re
from datetime import datetime
from typing import List

import py_stealth as stealth
from tools import constants
from global_logger import Log
log = Log.get_logger(use_colors=False)


def debug():
    try:
        # pylint: disable=import-error
        import pydevd_pycharm  # noqa: E402
    except:
        os.system('pip install -U pydevd-pycharm')
        return debug()

    ip = 'localhost'
    port = 12345
    print("Connecting to PyCharm Debugger @ %s:%s" % (ip, port))
    try:
        pydevd_pycharm.settrace(ip, port=port, stdoutToServer=True, stderrToServer=True, suspend=False)
    except Exception as e:
        print("Error connecting to PyCharm Debugger @ %s:%s : %s %s" % (ip, port, type(e), e))
    else:
        print("Connected to PyCharm Debugger @ %s:%s" % (ip, port))
    log.verbose = True


DEBUG = True
if DEBUG:
    debug()


def get_prev_function_name():
    stack = inspect.stack()
    stack1 = stack[2]
    output = stack1[3]
    return output


def in_journal(text, regexp=False, return_re_value=False, limit_last=50, from_index=None, to_index=None,
               journal_lines=None):
    """Returns whether the supplied text is ANYWHERE in the journal"""
    if journal_lines is None:
        high_journal = stealth.HighJournal() if to_index is None else to_index
        low_journal = stealth.LowJournal() if from_index is None else from_index
        if limit_last:
            low_journal = high_journal - limit_last
        range_ = range(low_journal, high_journal + 1)
        if len(range_) > 55:
            log.info(f"Parsing too long journal: {low_journal} to {high_journal} range {range_} for text: {text}")
        journal_lines = [constants.JournalLine(i) for i in range_]
    for line in journal_lines:
        output = line.contains(text, regexp=regexp, return_re_value=return_re_value)
        if output:
            return output

    return False


def telegram_message(msg, chat_id=None, disable_notification=False, token=None):
    if not msg:
        return

    token = token or os.getenv('STEALTH_TELEGRAM_TOKEN')
    if token and not token.startswith('bot'):
        token = f"bot{token}"
    if not token:
        return

    chat_id = chat_id or os.getenv('STEALTH_TELEGRAM_CHAT_ID')
    if not chat_id:
        return

    disable_notification = str(disable_notification).lower()
    cmd = f'curl -X POST "https://api.telegram.org/{token}/sendMessage" -d chat_id={chat_id} ' \
          f'-d disable_notification={disable_notification} -d text="{msg}"'
    return os.system(cmd)


def _delay(delay=250):
    return stealth.Wait(delay)


def ping_delay():
    return _delay(250)


def result_delay():
    return _delay(500)


def useobject_delay():
    return _delay(constants.USE_COOLDOWN)


def string_in_strings(str_, strings):
    return any(i for i in strings if str_.lower() in i.lower())


def journal(start_index=None, end_index=None):
    start_index = stealth.LowJournal() if start_index is None else start_index
    end_index = stealth.HighJournal() if end_index is None else end_index
    line_numbers = range(start_index, end_index + 1)
    output = []
    for line_number in line_numbers:
        output.append(constants.JournalLine(line_number))
    return output


def journal_lines_for_timedelta(self, start: datetime, end: datetime) -> List[constants.JournalLine]:
    potential_end_index = stealth.InJournalBetweenTimes(' ', start, end)
    end_index = None if potential_end_index in (-1, None) else potential_end_index + 1
    return [line for line in self._journal(end_index=end_index) if start <= line.time <= end]


def __main():
    telegram_message('test message')


if __name__ == '__main__':
    __main()
