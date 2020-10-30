import numpy
import scipy.optimize


def leastsq(*args, **args2):
    """Least squares returns a scalar if the lenght of the
        params is 1, make it consistent by always returning array"""
    result, success = scipy.optimize.minpack.leastsq(*args, **args2)
    if numpy.isscalar(result):
        result = numpy.array([result])
    return result, success
