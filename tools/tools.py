import inspect
import os
import re

from py_stealth import *

log = AddToSystemJournal


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


def get_prev_function_name():
    stack = inspect.stack()
    stack1 = stack[2]
    output = stack1[3]
    return output


def in_journal(text, regexp=False, return_re_value=False):
    """Returns whether the supplied text is ANYWHERE in the journal"""
    for line in [Journal(i) for i in range(0, HighJournal() + 1)]:
        if regexp:
            if re.search(text, line, re.IGNORECASE | re.MULTILINE):
                if return_re_value:
                    return re.findall(text, line)
                else:
                    return True
        else:
            if text.lower() in line.lower():
                return True

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
    return Wait(delay)


def ping_delay():
    return _delay(250)


def result_delay():
    return _delay(500)


def __main():
    telegram_message('test message')


if __name__ == '__main__':
    __main()
