def combinations(items, unique=True, n=None):
    """All permutations of length n, without duplication, from items"""

    if n is None:
        for n in range(len(items) + 1):
            for value in combinations(items, n=n, unique=unique):
                yield value
    else:
        if n == 0:
            yield []
        else:
            for i in range(len(items)):
                if unique:
                    for comb in combinations(items[i + 1:], n=n - 1,
                                             unique=unique):
                        yield [items[i]] + comb
                else:
                    for comb in combinations(items[i:], n=n - 1,
                                             unique=unique):
                        yield [items[i]] + comb
