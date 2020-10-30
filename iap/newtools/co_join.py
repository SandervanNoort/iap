def co_join(values):
    """Join a list to feed it to configobj"""
    if len(values) == 0:
        return ","
    elif len(values) == 1:
        return "{0},".format(values[0])
    else:
        return ", ".join(["{0}".format(elem) for elem in values])
