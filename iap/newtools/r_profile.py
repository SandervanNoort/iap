import os
import rpy2


def r_profile():
    rprofile = os.path.join(os.path.expanduser("~"), ".Rprofile")
    if os.path.exists(rprofile):
        with open(rprofile) as fobj:
            rpy2.robjects.r(fobj.read())
