from entities.item import Item, stealth
from tools import tools, constants
from tools.tools import log


class Container(Item):
    def __init__(self, _id, **kwargs):
        super().__init__(_id, **kwargs)
        if _id == 0:
            self.name = 'Ground'

    def __str__(self):
        return f"[{self.__class__.__name__}]({hex(self._id)}){self.name}"

    @property
    def is_empty(self):
        items = stealth.FindType(-1, self._id)
        return not items

    @property
    def is_container(self):
        return stealth.IsContainer(self._id)

    def _get_click_info(self):
        journal_start = stealth.HighJournal() + 1
        stealth.ClickOnObject(self._id)
        journal = tools.journal(start_index=journal_start)
        journal_filtered = [i for i in journal if 'You see: ' in i.text]
        return journal_filtered

    @property
    def innocent(self):
        return any(i for i in self._get_click_info() if i.color == constants.LineColor.INNOCENT)

    @property
    def locked(self):
        return any(i for i in self._get_click_info()
                   if i.color == constants.LineColor.WHITE
                   and 'locked down' in i.text.lower())

    @property
    def secure(self):
        return any(i for i in self._get_click_info()
                   if i.color == constants.LineColor.WHITE
                   and 'secure' in i.text.lower())


if __name__ == '__main__':
    container = Container.instantiate('0x4A8F022F')
    empty = container.is_empty
    pass
