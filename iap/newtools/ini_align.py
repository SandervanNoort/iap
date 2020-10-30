import re
from .Cache import Cache


def ini_align(fobj):
    """make a nicely aligned ini file"""
    output = ""
    tab = "    "
    cache = Cache()
    indent = 0
    keys = []
    vals = []

    def key_lines(keys, vals, indent):
        """Print the key=val aligned on the '=' """
        key_output = ""
        if not keys:
            return key_output
        size = max([len(key) for key in keys])
        for key, val in zip(keys, vals):
            if val is None:
                key_output += key + "\n"
            else:
                key_output += "{indent}{key}{pad}={val}\n".format(
                    indent=tab * indent,
                    key=key,
                    pad=(size-len(key)) * " ",
                    val=val)
        return key_output

    for line in fobj.decode("utf8").split("\n"):
        if cache(re.match(r" *(\[+)", line)):
            output += key_lines(keys, vals, indent)
            keys, vals = [], []
            indent = len(cache.output.group(1))
            output += tab * (indent - 1) + line + "\n"
        else:
            if "=" in line:
                key, val = re.split("=", line, 1)
                keys.append(key)
                vals.append(val)
            else:
                keys.append(line)
                vals.append(None)
    output += key_lines(keys, vals, indent)
    return output.strip() + "\n"
