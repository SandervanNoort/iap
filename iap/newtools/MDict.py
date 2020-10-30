class MDict(dict):
    """A dictionionary which returns self.missing (default=0)
        for non existing value
        The advantage over collections.defaultdict(int), is
        that the key is not filled when a unknown key is requested.
    """

    def __init__(self, **kwargs):
        self.missing = kwargs.pop("missing", 0)
        dict.__init__(self, kwargs)

    def __missing__(self, _key):
        """Return self.missing when missing key"""
        return self.missing
