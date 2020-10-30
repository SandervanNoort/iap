import io
import six
import pickle


def numpy_load(fname):
    """Load numpy files"""
    import numpy
    if six.PY3:
        with io.open(fname, "rb") as fobj:
            return pickle.load(fobj, encoding="latin1")
    else:
        return numpy.load(fname)
