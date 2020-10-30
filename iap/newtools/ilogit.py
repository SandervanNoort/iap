import numpy


def ilogit(value):
    """Inverse logit"""
    # -inf,inf => 0,1
    return 1 / (1 + numpy.exp(-value))
