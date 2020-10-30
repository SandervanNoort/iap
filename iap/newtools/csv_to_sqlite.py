import logging

from .sqlite_table_exists import sqlite_table_exists
from .csvopen import csvopen
from .ureader import ureader
from .normalize import normalize


def csv_to_sqlite(conn, csv_name, table, col_types=None, sep=","):
    """Convert csv to SQL"""

    if col_types is None:
        col_types = {}

    if sqlite_table_exists(conn, table):
        logging.info("Table %s already exists", table)
        return

    logging.info("Creating table %s", table)
    with csvopen(csv_name, "r") as fobj:
        reader = ureader(fobj, delimiter=sep)
        headers = next(reader)
        columns = [
            "{colname} {coltype}".format(
                colname=normalize(header),
                coltype=col_types.get(header, "text"))
            for header in headers]
        conn.execute("CREATE TABLE {table} ({columns})".format(
            columns=",".join(columns), table=table))
        conn.executemany(
            "INSERT INTO {table} VALUES ({values})".format(
                table=table,
                values=",".join(len(headers) * ["?"])),
            reader)
        conn.commit()
