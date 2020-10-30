#!/usr/bin/env python3

import matplotlib.font_manager
import shutil

dirname = matplotlib.font_manager.get_cachedir()
print("Clearing font dir: {}".format(dirname))
shutil.rmtree(dirname)