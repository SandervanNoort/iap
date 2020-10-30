import itertools


def get_subsets(mylist):
    """Return all subsets"""

    return itertools.chain(*(itertools.combinations(mylist, size)
                             for size in range(len(mylist), -1, -1)))
