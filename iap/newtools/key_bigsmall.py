import re


def key_bigsmall(line):
    """Replace >a and <b by a+1 an b-1"""
    def replace(match):
        """inline replace function"""
        if match.group(1) == ">":
            return "{0}".format(int(match.group(2)) + 1)
        elif match.group(1) == "<":
            return "{0}".format(int(match.group(2)) - 1)
    return re.sub(r"([<>])(\d+)", replace, line)
