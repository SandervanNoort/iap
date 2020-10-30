class Lazy(object):
    """Object which is only run when str representation
        f.e.: logger.debug(run_function)
        http://stackoverflow.com/questions/4148790
            /lazy-logger-message-string-evaluation"""
    # (too few public methods) pylint: disable=R0903

    def __init__(self, func):
        self.func = func

    def __str__(self):
        return self.func()
