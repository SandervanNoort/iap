import os
import re


def var_substitute(fname, values):
    """Substitute the variable declarations"""

    with open(os.path.join(fname), "r") as fobj:
        contents = fobj.read()
        for key, value in values.items():
            contents = re.sub(
                "{0} *=.*".format(key),
                "{0} = \"{1}\"".format(key, value),
                contents)
    with open(os.path.join(fname), "w") as fobj:
        fobj.write(contents)
