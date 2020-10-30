import configobj


def cobj_update(orig, new):
    """Recursive update"""
    for entry in new:
        if isinstance(new[entry], configobj.Section):
            cobj_update(orig[entry], new[entry])
        else:
            orig[entry] = new[entry]
