import numpy


def perm(lists, perms=None):
    """All unique combinations fom elems from all lists"""
    if lists == []:
        return numpy.array(perms)
    else:
        add_list = lists.pop(0)
        if perms is None:
            perms = [[]]
        return perm(lists, [perms_elem + [add_elem]
                            for perms_elem in perms
                            for add_elem in add_list])
