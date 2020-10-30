import six
import io

if six.PY2:
    def csvopen(*args, **kwargs):
        """define open(), with binary for python2"""
        if len(args) > 1 and "b" not in args[1]:
            args = list(args)
            args[1] += "b"
        if "mode" in kwargs and "b" not in kwargs["mode"]:
            kwargs["mode"] += "b"
        return io.open(*args, **kwargs)
else:
    csvopen = io.open
