from typing import Tuple

import jdcal
from datetime import datetime


def julian_timestamp(dt: datetime) -> int:
    julian_day_start = jdcal.gcal2jd(dt.year, dt.month, dt.day)
    fraction_of_day = (dt.hour*3600 + dt.minute*60 + dt.second) / (24*3600)
    return sum(julian_day_start) + fraction_of_day


def sec2pixel(arc_s: int, image_px: int, field_s: int) -> int:
    """
    Given dimensions of an image in pixels and arcseconds, translate
    `arc_s` of arcseconds to pixels.

    :param arc_s: arcseconds to traslate
    :param image_px: dimension in pixels
    :param field_s: dimension in arcseconds

    Usage:
    >>> sec2pixel(10, 100, 100)
    10
    >>> sec2pixel(20, 100, 100)
    20
    >>> sec2pixel(10, 1000, 100)
    100
    """
    scale = image_px / field_s
    return int(round(arc_s * scale))


def fitting_scale(
        frame_w: int, frame_h: int, content_w: int, content_h: int
) -> (float, float):
    """
    Calculate scaling factor for content so that it fits the frame.

    :param frame_w: width of the frame
    :param frame_h: height of the frame
    :param content_w: width of the content
    :param content_h: height of the content

    Usage:
    >>> fitting_scale(50, 50, 100, 100)
    0.5
    >>> fitting_scale(50, 50, 50, 100)
    0.5
    >>> fitting_scale(50, 50, 100, 50)
    0.5
    >>> fitting_scale(50, 50, 50, 50)
    1.0
    >>> fitting_scale(50, 50, 10, 10)
    5.0
    >>> fitting_scale(50, 50, 25, 10)
    2.0
    >>> fitting_scale(50, 50, 10, 25)
    2.0
    """
    frame_ratio = frame_w / frame_h
    content_ratio = content_w / content_h
    if frame_ratio > content_ratio:
        return frame_h / content_h
    else:
        return frame_w / content_w
