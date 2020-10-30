import collections
import numpy


def get_conf_poisson(hits, totals, factors=None, sumall=False):
    """Get the confidence interval (+/- sigma), weight with factors"""

    if not isinstance(hits, collections.Iterable):
        hits = [hits]
    if not isinstance(totals, collections.Iterable):
        totals = [totals]
    if factors is None:
        factors = [1] * len(hits)
    if not isinstance(factors, collections.Iterable):
        factors = [factors]

    weights = factors if sumall \
        else [factor / sum(factors) for factor in factors]
    prop = sum([weight * hit / total
                for hit, total, weight in zip(hits, totals, weights)])
    sigma = sum([hit * (weight / total) ** 2
                 for hit, total, weight in zip(hits, totals, weights)]) ** 0.5
    return numpy.array([prop - sigma, prop, prop + sigma])
