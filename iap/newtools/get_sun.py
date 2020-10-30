import sys
import ephem


def get_sun(country, date):
    """Return sunlight hours"""
    city = ephem.city(
        "Amsterdam" if country == "nl" else
        "Lisbon" if country == "pt" else
        "Amsterdam" if country == "be" else
        "")
    if city == "":
        sys.exit("Unknown country")
    sun = ephem.Sun()  # pylint: disable=E1101
    city.date = date
    date_rise = city.next_rising(sun).datetime()
    date_set = city.next_setting(sun).datetime()
    print(date_rise, date_set)
    return (date_set - date_rise).seconds / 3600.
