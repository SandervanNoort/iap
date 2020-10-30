import os


def file_exists(name):
    """none: file does not exists
        file: file does exist
        broken: file is a broken sublink
        """

    try:
        os.lstat(name)
    except OSError:
        return "none"

    if os.path.exists(name):
        return "file"
    else:
        return "broken"
