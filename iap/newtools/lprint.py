def lprint(mylist, string_format):
    """Print a list value with string_format"""
    return ",".join([string_format.format(val) for val in mylist])
