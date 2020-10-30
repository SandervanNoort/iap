import os


def clear_empty_dirs(dirname):
    """Clear (recursively) all empty directories"""

    deleted = 0
    for dirpath, dirnames, fnames in os.walk(dirname):
        if len(dirnames) == 0 and len(fnames) == 0:
            os.removedirs(dirpath)
            deleted += 1
    if deleted > 0:
        clear_empty_dirs(dirname)
