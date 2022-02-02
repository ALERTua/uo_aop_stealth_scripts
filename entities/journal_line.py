# do not import tools here
import re
from enum import unique, Enum

import py_stealth as stealth


class JournalLine:
    def __init__(self, journal_id):
        self.journal_id = journal_id
        self.text = stealth.Journal(self.journal_id)
        self.color = stealth.LineTextColor()
        try:
            self.color = LineColor(self.color)
        except:
            pass

        self.author = stealth.LineName()
        self.time = stealth.LineTime()
        # self.msg_type = LineMsgType()
        # self.count = LineCount()
        # self.line_id = LineID()
        # self.type = LineType()
        # self.font = LineTextFont()

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.__str__()

    def contains(self, text, regexp=False, return_re_value=False):
        if regexp:
            if re.search(text, self.text, re.IGNORECASE | re.MULTILINE):
                if return_re_value:
                    return re.findall(text, self.text, re.IGNORECASE | re.MULTILINE)
                else:
                    return True
        else:
            if text.lower() in self.text.lower():
                return True

        return False


@unique
class LineColor(Enum):
    GREY = 946
    INNOCENT = 90
    RED = 38
    SPEECH = 690
    YELLOW = 55
    WHITE = 1153
