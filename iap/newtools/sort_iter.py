import natsort


def sort_iter(mydict, natural=False, **kwargs):
    """Iter through a dict, sorted by the key"""
    for key in (natsort.natsorted(mydict.keys()) if natural else
                sorted(mydict.keys(), **kwargs)):
        yield key, mydict[key]
