def sql_bracket(sql):
    """Add brackets to sql string"""

    if (len(sql) == 0 or
            " " not in sql):
            # sql[0] == "(" and sql[-1] == ")"):
        return sql
    else:
        return "({0})".format(sql)
