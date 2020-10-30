import numpy
from .leastsq import leastsq


def fit_params(values, times, function, params_guess):
    """Find the best params using least squares"""
    def get_difs(params):
        """The difference between function(params) and values"""
        return numpy.array(values) - numpy.array(
            [function(week, params) for week in times])
    params, _succes = leastsq(get_difs, params_guess)
    return params
