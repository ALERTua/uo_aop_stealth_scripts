# do not import tools here
import re
from enum import unique, Enum

import py_stealth as stealth


class JournalLine:
    def __init__(self, journal_id):
        self.journal_id = journal_id
        self.text = stealth.Journal(self.journal_id)  # type: str
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
        return f"({self.journal_id}){self.text}"

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

    @property
    def system(self):
        text = self.text
        if not text:
            return False

        return text.startswith('System:')

    @property
    def text_clean(self):
        text = self.text
        if not text or ':' not in text:
            return text

        output = text.split(':')
        output = output[1:]
        output = " ".join(output)
        output = output.strip()
        return output


@unique
class LineColor(Enum):
    GREY = 946
    INNOCENT = 90
    RED = 38
    SPEECH = 690
    YELLOW = 55
    WHITE = 1153
