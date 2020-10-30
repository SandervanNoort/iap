import string
import re
from .Cache import Cache
from .co_join import co_join


class Format(string.Formatter):
    """Specific format class, with extras"""

    def __init__(self, format_string="", default=None):
        string.Formatter.__init__(self)
        self.format_string = format_string
        self.default = default

    def get_value(self, key, args, kwargs):
        """Get the value from the supplied arguments
           (or default)"""
        if self.default is not None:
            try:
                return string.Formatter.get_value(self, key, args, kwargs)
            except KeyError:
                return self.default
        else:
            return string.Formatter.get_value(self, key, args, kwargs)

    def format_field(self, value, spec):
        """Format the string (with configobj "co" syntax)"""
        cache = Cache()
        if spec == "co":
            # if cache(re.match("(.*)co$", spec)):
            value = co_join(value)
            spec = "s"
            # cache.output.group(1) + "s"
        elif cache(re.match(r"^sub(\d?)_?(.*)$", spec)):
            depth = (1 if cache.output.group(1) == "" else
                     int(cache.output.group(1)))
            value = "\n".join([
                "{0}{1} = {2}".format(depth * "    ", key, val)
                for key, val in value.items()])
            if cache.output.group(2) != "":
                value = (
                    depth * "[" + cache.output.group(2) + depth * "]" + "\n" +
                    value)
            spec = "s"
        return super(Format, self).format_field(value, spec)

    def format(self, extra=None, *args, **kwargs):
        """The format function with the extras"""
        if extra is not None:
            for key, value in extra.items():
                if key not in kwargs:
                    kwargs[key] = value
        return super(Format, self).format(self.format_string, *args, **kwargs)
