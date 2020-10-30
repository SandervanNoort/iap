import csv
import xlrd
import six

from .csvopen import csvopen
from .uwriter import uwriter


def xls_to_csv(xls_fname, csv_fname, index=0, name=None):
    workbook = xlrd.open_workbook(xls_fname)
    if isinstance(name, list):
        sheet_names = workbook.sheet_names()
        test_names = list(name)
        name = None
        for test_name in test_names:
            if test_name in sheet_names:
                name = test_name
    worksheet = (workbook.sheet_by_name(name) if name is not None else
                 workbook.sheet_by_index(index))
    csvobj = csvopen(csv_fname, "w")
    writer = uwriter(csvobj, quoting=csv.QUOTE_ALL)
    for row_number in range(worksheet.nrows):
        writer.writerow(worksheet.row_values(row_number))
    csvobj.close()
