import inspect
import math
import os
import traceback
import unicodedata
import numpy as np
import requests
from datetime import datetime
from typing import List
import ping3

from entities.journal_line import JournalLine
import py_stealth as stealth

from global_logger import Log
log = Log.get_logger(use_colors=False)
_server_ip = None
_server_ping_average = {}


def debug(ip=None):
    try:
        # pylint: disable=import-error
        import pydevd_pycharm  # noqa: E402
    except:
        os.system('pip install -U pydevd-pycharm')
        return debug(ip=ip)

    ip = ip or 'localhost'
    port = 12345
    log.info("Connecting to PyCharm Debugger @ %s:%s" % (ip, port))
    try:
        pydevd_pycharm.settrace(ip, port=port, stdoutToServer=True, stderrToServer=True, suspend=False)
    except Exception as e:
        print("Error connecting to PyCharm Debugger @ %s:%s : %s %s" % (ip, port, type(e), e))
        log.verbose = False
        return False

    log.info("Connected to PyCharm Debugger @ %s:%s" % (ip, port))
    log.verbose = True
    return True


DEBUG = True
if DEBUG:
    debug() or debug('192.168.1.2')


def get_function_name():
    return traceback.extract_stack(None, 2)[0][2]


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
        journal_lines = [JournalLine(i) for i in range_]
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

    data = {
        'text': msg,
        'chat_id': chat_id,
        'parse_mode': 'html',
        'disable_notification': disable_notification
    }
    url = f'https://api.telegram.org/{token}/sendMessage'
    return requests.post(url=url, json=data)


def delay(ms=250):
    threshold = 5000
    if ms >= threshold:
        log.debug(f"Delay {ms} from {get_prev_function_name()}")
    stealth.Wait(ms)
    if ms >= threshold:
        log.debug(f"Delay {ms} from {get_prev_function_name()} finished")


def ping_delay():
    return delay(server_ping_average() + 10)


def result_delay():
    return delay(server_ping_average() * 2 + 100)


def string_in_strings(str_, strings):
    return any(i for i in strings if str_.lower() in i.lower())


def journal(start_index=None, end_index=None):
    start_index = stealth.LowJournal() if start_index is None else start_index
    end_index = stealth.HighJournal() if end_index is None else end_index
    line_ids = range(start_index, end_index + 1)
    output = []
    for line_id in line_ids:
        line = JournalLine(line_id)
        if line.text:
            output.append(line)
    return output


def journal_lines_for_timedelta(self, start: datetime, end: datetime) -> List[JournalLine]:
    potential_end_index = stealth.InJournalBetweenTimes(' ', start, end)
    end_index = None if potential_end_index in (-1, None) else potential_end_index + 1
    return [line for line in self._journal(end_index=end_index) if start <= line.time <= end]


def server_ip():
    global _server_ip
    if _server_ip is None:
        _server_ip = stealth.GameServerIPString()
    return _server_ip


def server_ping(ip=None):
    fallback = 250
    ip = ip or server_ip()
    ping = ping3.ping(ip)
    if not ping:
        return fallback

    ping *= 1000
    ping = round(ping, 0)
    ping = int(ping)
    return ping


def server_ping_average(ip=None, iterations=5, singleton=True):
    def _ping_average(_ip, _iterations):
        pings = []
        for _ in range(_iterations):
            ping = server_ping(ip=_ip)
            pings.append(ping)

        _output = sum(pings) / len(pings)
        _output = round(_output, 0)
        _output = int(_output)
        return _output

    if singleton:
        global _server_ping_average
        if _server_ping_average.get(ip) is None:
            _server_ping_average[ip] = _ping_average(_ip=ip, _iterations=iterations)
            log.debug(f"Setting server IP {ip} {iterations} pings average to {_server_ping_average[ip]}")
        return _server_ping_average[ip]

    output = _ping_average(_ip=ip, _iterations=iterations)
    log.debug(f"Returning server IP {ip} {iterations} pings average: {output}")
    return output


def circle_points(start_x, start_y, radius, angle_step=30):
    for angle in range(0, 360, angle_step):
        angle_rad = angle * math.pi / 180
        x = start_x + radius * math.cos(angle_rad)
        y = start_y + radius * math.sin(angle_rad)
        yield int(x), int(y)


def coords_array_closest(starting_coords, coords_array):
    coords = np.asarray(coords_array)
    deltas = coords - starting_coords
    dist_2 = np.einsum('ij,ij->i', deltas, deltas)
    return dist_2.argsort()


def reconnect():
    stealth.Disconnect()
    delay(7000)


def is_latin(word):
    return all(['LATIN' in unicodedata.name(c) for c in word])


def __main():
    telegram_message('test message')


if __name__ == '__main__':
    __main()
