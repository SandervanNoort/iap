import re
import datetime


def get_date(datestring):
    """"Return the date based on a string"""
    elements = [int(a) for a in re.split("[-/]", "{0}".format(datestring))]
    if len(elements) == 3:
        return datetime.date(elements[0], elements[1], elements[2])
