class ListIO(object):
    """Like stringIO, but keeps a list"""
    # (too few public methods) pylint: disable=R0903

    def __init__(self, values, key):
        self.values = values
        self.key = key

    def write(self, value, *_args, **_kwargs):
        """Write output to the list"""
        self.values.append([self.key, value])
