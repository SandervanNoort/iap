class AddList(list):
    """A list class which sums over each element"""
    def __add__(self, list2):
        return AddList([item1 + item2 for item1, item2 in zip(self, list2)])

    def __iadd__(self, list2):
        return AddList([item1 + item2 for item1, item2 in zip(self, list2)])
