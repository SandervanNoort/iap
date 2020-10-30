def dates_string(date1, date2):
    """Readable string for a period"""

    day1 = date1.day
    day2 = date2.day

    month1 = date1.strftime("%b")
    month2 = date2.strftime("%b")

    year1 = date1.year
    year2 = date2.year

    if month1 == month2:
        result = "{d1} - {d2} {m1} {y1}"
    elif year1 == year2:
        result = "{d1} {m1} - {d2} {m2} {y1}"
    else:
        result = "{d1} {m1} {y1} - {d2} {m2} {y2}"
    return result.format(d1=day1, d2=day2, m1=month1, m2=month2,
                         y1=year1, y2=year2)
