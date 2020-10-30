import configobj


def add_section(orig_section, new_section):
    """Add a section to a configobj"""
    for key in new_section:
        if isinstance(new_section[key], configobj.Section):
            orig_section[key] = {}
            add_section(orig_section[key], new_section[key])
        else:
            orig_section[key] = new_section[key]
    # self[key].update(section)
