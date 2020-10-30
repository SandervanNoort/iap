import sys
import configobj


def deepcopy(obj):
    """Copy the section"""
    if type(obj) == configobj.Section:
        new_obj = configobj.Section(obj.parent, obj.depth, obj.main)
    elif type(obj) == configobj.ConfigObj:
        new_obj = configobj.ConfigObj()
    else:
        sys.exit("Copy for {0} not implemented".format(type(obj)))
    for scalar in obj.scalars:
        new_obj[scalar] = obj[scalar]
    for section in obj.sections:
        new_obj[section] = deepcopy(obj[section])
    new_obj.sections = list(obj.sections)
    new_obj.scalars = list(obj.scalars)
    return new_obj
