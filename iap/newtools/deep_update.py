import collections


def deep_update(orig, new):
    """recursive update of dict <orig> from value from dict <new>"""

    for key, value in new.iteritems():
        if isinstance(value, collections.Mapping):
            orig[key] = deep_update(orig.get(key, {}), value)
        else:
            orig[key] = new[key]
    return orig
