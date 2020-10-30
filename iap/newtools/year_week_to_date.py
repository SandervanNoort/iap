import sys
import datetime


def year_week_to_date(year, week, exception=None, weekday=7):
    """Return the date of weekday (1-7) of year/week"""

    if not exception:
        exception = Exception

    if year < 1900 or year > 2100:
        sys.exit("error in year '{0}'".format(year))
    if week < 1 or week > 53:
        sys.exit("error in week: '{0}'".format(week))

    day1 = datetime.timedelta(days=1)
    jan1 = datetime.date(year, 1, 1)
    weekday_jan1 = jan1.weekday() + 1
    day_week1 = jan1 + (weekday - weekday_jan1) * day1
    if weekday_jan1 > 4:
        day_week1 += 7 * day1
    day = day_week1 + 7 * (week - 1) * day1
    if (year, week, weekday) == day.isocalendar():
        return day
    else:
        raise exception("Invalid iso date: year {year}, week {week}".format(
            year=year, week=week))
