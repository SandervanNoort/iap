import rpy2
import six
import sys


def cwrapper(*args):
    """Shortcut for c() in R"""
    # (invalid name) pylint: disable=C0103
    if len(args) == 1 and isinstance(args[0], (list, tuple, set)):
        args = args[0]
    if all([isinstance(arg, int) or arg is None for arg in args]):
        return rpy2.robjects.IntVector([
            rpy2.rinterface.NA_Integer if arg is None else arg
            for arg in args])
    elif all([isinstance(arg, (int, float)) or arg is None for arg in args]):
        return rpy2.robjects.FloatVector([
            rpy2.rinterface.NA_Real if arg is None else arg
            for arg in args])
    elif all([isinstance(arg, six.string_types) or arg is None
              for arg in args]):
        return rpy2.robjects.StrVector(args)
    else:
        sys.exit("Unknown vector: {0}".format(args))
