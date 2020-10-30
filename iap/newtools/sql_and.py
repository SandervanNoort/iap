from .sql_bracket import sql_bracket


def sql_and(*args):
    """add extra to where-clause"""
    return " AND ".join([
        sql if index == 0 else sql_bracket(sql)
        for index, sql in enumerate(args)
        if sql != ""])
