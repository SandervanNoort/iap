def mysql_table_exists(cursor, table):
    """Table exists"""
    cursor = cursor.execute("SHOW TABLES LIKE %s", (table,))
    cursor.commit()
    return cursor.rowcount > 0
