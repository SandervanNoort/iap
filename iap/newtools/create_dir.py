import os
import shutil
import six


def create_dir(fname, remove=False, is_dir=False, is_file=False):
    """If the directory for fname does not exists, create it"""

    if not isinstance(fname, six.string_types):
        print("cannot create_dir for {0}".format(fname))
        return

    dirname = os.path.dirname(fname)
    if is_file:
        dirname = dirname
    elif is_dir:
        dirname = fname
    elif os.path.splitext(fname)[1] == "":
        dirname = fname

    if os.path.exists(fname) and remove:
        if os.path.islink(fname) or os.path.isfile(fname):
            os.remove(fname)
        else:
            shutil.rmtree(fname)
    if dirname != "" and not os.path.exists(dirname):
        os.makedirs(dirname)
