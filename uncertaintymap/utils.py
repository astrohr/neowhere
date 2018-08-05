import jdcal
from datetime import datetime


def julian_timestamp(dt: datetime):
    julian_day_start = jdcal.gcal2jd(dt.year, dt.month, dt.day)
    fraction_of_day = (dt.hour*3600 + dt.minute*60 + dt.second) / (24*3600)
    return sum(julian_day_start) + fraction_of_day
