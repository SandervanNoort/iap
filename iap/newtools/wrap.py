import re
import textwrap


def wrap(text, size=20):
    """Break up string by whitespaces, returning multi-line string"""
    if isinstance(text, list):
        return [wrap(item) for item in text]
    # respect newlines already present
    if size == 0 or len(text) <= size:
        return text
    return "\n".join(["\n".join(textwrap.wrap(subtext, size,
                                              break_long_words=False))
                      for subtext in re.split("\n|__|: ", text)])
