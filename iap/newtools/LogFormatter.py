import logging
import six


class LogFormatter(logging.Formatter):
    """Format logging message based on msg style"""

    def __init__(self, default_style, style_dict=None):
        logging.Formatter.__init__(self, default_style)
        self.style_dict = {} if style_dict is None else style_dict
        self.default_style = default_style

    def format(self, record):
        self._fmt = self.style_dict.get(record.levelno, self.default_style)
        if six.PY3:
            self._style = logging.PercentStyle(self._fmt)
        return logging.Formatter.format(self, record)
