from __future__ import (division, absolute_import, unicode_literals,
                        print_function)
import sys
import numpy
import scipy.stats
from .get_z import get_z


def get_prop(hits, n, alpha=0.05, method="jeffreys"):
    """Return proportion with confidence interval"""
    # http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
    # (Invalid name) pylint: disable=C0103

    if method == "all":
        return ["normal", "awald", "jeffreys", "clopper", "wilson",
                "wilson-continuity"]

    if n == 0:
        return [0, 0, 0]

    hits = min(hits, n)
    p = hits / n

    if method == "normal":
        # wald
        var = p * (1 - p) / n  # ~ hits/n**2
        error = get_z(1 - alpha / 2) * var ** 0.5
        min_p, max_p = p - error, p + error

    elif method == "awald":
        z = get_z(1 - alpha / 2)
        p = (hits + 2) / (n + 4)
        var = p * (1 - p) / (n + 4)
        min_p = p - z * var ** 0.5
        max_p = p + z * var ** 0.5
    elif method == "jeffreys":
        # nuno
        bnorm = scipy.stats.distributions.beta.ppf
        min_p = (0 if hits == 0 else
                 bnorm(alpha / 2, hits + 1 / 2, n - hits + 1 / 2))
        max_p = (1 if hits == n else
                 bnorm(1 - alpha / 2, hits + 1 / 2, n - hits + 1 / 2))
    elif method == "clopper":
        bnorm = scipy.stats.distributions.beta.ppf
        min_p = (0 if hits == 0 else
                 bnorm(alpha / 2, hits, n - hits + 1))
        max_p = (1 if hits == n else
                 bnorm(1 - alpha / 2, hits + 1, n - hits))
    elif method == "wilson":
        z = get_z(1 - alpha / 2)
        error = (z * numpy.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) /
                 (1 + z ** 2 / n))
        mean = (p + z ** 2 / (2 * n)) / (1 + z ** 2 / n)
        min_p = mean - error
        max_p = mean + error
    elif method == "wilson-continuity":
        z = get_z(1 - alpha / 2)
        mean = (p + z ** 2 / (2 * n)) / (1 + z ** 2 / n)
        error = ((z * numpy.sqrt(z ** 2 - 1 / n + 4 * n * p * (1 - p) +
                                 (4 * p - 2)) + 1) /
                 (2 * (n + z ** 2)))
        min_p = max(0, mean - error)
        max_p = min(1, mean + error)
    else:
        sys.exit("Unknown prop method: {0}".format(method))

    return min_p, p, max_p
