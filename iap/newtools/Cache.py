class Cache(object):
    """Class which save output when called"""
    # (too few public methods) pylint: disable=R0903

    def __init__(self):
        self.output = None

    def __call__(self, output):
        self.output = output
        return output
