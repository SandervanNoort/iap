import sys


class Delayed(object):
    """Class which will delayed add variable/attributes"""
    # pylint: disable=R0903
    def __init__(self, name, init_func):
        self.module = sys.modules[name]
        self.init_func = init_func
        sys.modules[name] = self
        self.initializing = True

    def __getattr__(self, name):
        # call module.__init__ after import introspection is done
        if self.initializing and not name[:2] == '__' == name[-2:]:
            self.initializing = False
            self.init_func(self.module)
        return getattr(self.module, name)
