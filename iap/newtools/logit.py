import numpy


def logit(prob):
    """Logit transform"""
    # 0,1 => -inf, +inf
    if prob == 1:
        return numpy.inf
    else:
        return numpy.log(prob / (1 - prob))
