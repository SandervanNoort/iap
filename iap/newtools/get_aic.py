import numpy


def get_aic(rss, n, p, corrected=True):
    """Return akaike info criterium"""
    # (invalid name) pylint: disable=C0103
    if corrected:
        p *= (p + 1) / (n - p - 1)
    return n * numpy.log(2 * numpy.pi) + n * numpy.log(rss / n) + n + 2 * p
