import re


def replace_multiple(text, word_dict, word_rc=None):
    """Replace multiple occurences in the same word"""
    if word_rc is None:
        word_rc = re.compile('|'.join([re.escape[word]
                                       for word in word_dict]))

    def translate(match):
        """Replace match with a word"""
        return "{0}".format(word_dict[match.group(0)])
    return word_rc.sub(translate, text)
