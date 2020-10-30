import math


def remove_nan(*args):
    """From various lists, remove the indexes where a number is NaN"""

    indeces = set([])
    for mylist in args:
        for index, elem in enumerate(mylist):
            if math.isnan(elem):
                indeces.add(index)
    for index in sorted(list(indeces), reverse=True):
        for mylist in args:
            mylist.pop(index)
