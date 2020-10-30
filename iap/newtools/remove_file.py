import os
import subprocess
import shutil


def remove_file(fname):
    """Remove a file, asking root if necessary"""

    if os.path.islink(fname) or os.path.isfile(fname):
        try:
            os.remove(fname)
        except OSError:
            try:
                subprocess.check_call(
                    "sudo rm \"{0}\"".format(fname), shell=True)
            except subprocess.CalledProcessError:
                print("Error removing {0}".format(fname))
    elif os.path.isdir(fname):
        try:
            shutil.rmtree(fname)
        except OSError:
            try:
                subprocess.check_call(
                    "sudo rm -R \"{0}\"".format(fname), shell=True)
            except subprocess.CalledProcessError:
                print("Error removing {0}".format(fname))
