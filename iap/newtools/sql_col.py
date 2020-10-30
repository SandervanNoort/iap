import re


def sql_col(column):
    """Column name which is valid in mysql"""
    return re.sub(r"[\[\]=>\- /]", "", column)
