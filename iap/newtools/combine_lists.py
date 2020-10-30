def combine_lists(lists):
    """All lists with at position 0, one element of lists[0], etc"""

    if len(lists) == 1:
        return lists[0]
    else:
        return combine_lists([[i + j for i in lists[0]
                               for j in lists[1]]] + lists[2:])
