import datetime


def daterange(start_date, end_date, step=1):
    """Iterage for a range of dates"""

    date = start_date
    while (date < end_date and step > 0) or (date > end_date and step < 0):
        yield date
        if isinstance(step, int):
            date += datetime.timedelta(days=step)
        elif step == "month":
            if date.month == 12:
                date = date.replace(month=1, year=date.year + 1)
            else:
                date = date.replace(month=date.month + 1)
        else:
            print("ERROR: step should be a number of days, or month")
            return
