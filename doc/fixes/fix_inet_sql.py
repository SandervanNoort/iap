#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Fix bad encodings from sql"""

from __future__ import division, absolute_import, unicode_literals

import codecs
import re
import os

from tools import tools
print(dir(tools))
sys.exit()

def fix(fname, chop=4):
    """Fix a sql file"""

    fobj_in = codecs.open(fname, "r", encoding="utf8")
    fobj_out = codecs.open(os.path.join("new", fname), "w", encoding="utf8")
    for line in fobj_in:
        fobj_out.write(
            re.sub(
                "\0", "\\\\'",
                re.sub(
                    "'(.*?)'", lambda match: "'{0}'".format(
                        tools.fix_bad_unicode(match.group(1), chop)),
                    re.sub("\\\\'", "\0", line))))
    fobj_in.close()
    fobj_out.close()

if __name__ == "__main__":
    tools.create_dir("new")
    fix("pt05.sql")
    # fix("pt06.sql")
    # fix("pt07.sql")
    # fix("it08.sql")
