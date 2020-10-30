from .is_na import is_na


def uncwrapper(rvector):
    """Convert R vector to python list"""
    return [None if is_na(elem) else elem
            for elem in rvector]
