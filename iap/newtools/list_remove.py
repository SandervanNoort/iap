from .get_iter import get_iter

def list_remove(alist, items):
    """Remove items from a list"""
    for item in get_iter(items):
        while item in alist:
            alist.remove(item)
