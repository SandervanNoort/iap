import collections


class SetList(list):
    """Class which keeps all elements unique"""

    def __init__(self, init_list=None):
        list.__init__(self)
        if init_list is not None:
            for elem in init_list:
                self.append(elem)

    def __add__(self, list2):
        new = SetList(self)
        for elem in self._get_iter(list2):
            new.append(elem)
        return new

    @staticmethod
    def _get_iter(list2):
        """Return iterable list"""
        if not isinstance(list2, collections.Iterable):
            return [list2]
        else:
            return list2

    def __iadd__(self, list2):
        for elem in self._get_iter(list2):
            self.append(elem)
        return self

    def __sub__(self, list2):
        new = SetList(self)
        for elem in self._get_iter(list2):
            if elem in new:
                new.remove(elem)
        return new

    def __isub__(self, list2):
        for elem in self._get_iter(list2):
            if elem in self:
                self.remove(elem)
        return self

    def append(self, elem):
        if elem not in self:
            list.append(self, elem)

    def extend(self, list2):
        for elem in list2:
            self.append(elem)
