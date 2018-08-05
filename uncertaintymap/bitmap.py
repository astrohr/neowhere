from contextlib import suppress
from math import floor
from typing import List, Tuple, Generator, Union, Optional

from PIL import Image


class Orbmap:

    def __init__(
            self,
            width: int, height: int,
            angle_seconds_ra: int, angle_seconds_de: int,
            ra_off_s: int, de_off_s: int,
            points: List[Tuple[int, int, str]],
            bg_color: Optional[Union[str, Tuple[int, int, int]]],
    ):
        self.w = width
        self.h = height
        self.ra_s = angle_seconds_ra
        self.de_s = angle_seconds_de
        self.center_ra_off = ra_off_s
        self.center_de_off = de_off_s
        # TODO field rotation angle
        self.points = points
        self.bg_color = bg_color
        if self.bg_color is None:
            self.bg_color = 'white'
        self.img = Image.new('RGB', (self.w, self.h), self.bg_color)
        self.colors = {
            'green': (46, 111, 22),
            'orange': (235, 106, 45),
            'red': (229, 32, 39),
            'blue': (32, 70, 246),
            'black': (
                (0, 0, 0) if sum(self.bg_color) > 3 * 128
                else (255, 255, 255)),
        }

    def sec2pixel(self, arc_s: int, x_or_y: str):
        if x_or_y == 'x':
            scale = self.w / self.ra_s
        elif x_or_y == 'y':
            scale = self.h / self.de_s
        else:
            raise ValueError('x_or_y can be either "x" or "y"')
        return int(round(arc_s * scale))

    def draw(self):
        for point in self.data:
            self.draw_marker(point)

    def save(self, file_path: str):
        self.img.save(file_path)

    def draw_marker(self, point: Tuple[int, int, str]):
        x, y, color_name = point
        color = self.colors[color_name]
        with suppress(IndexError):
            self.img.putpixel((x-1, y-1), color)
        with suppress(IndexError):
            self.img.putpixel((x+0, y-1), color)
        with suppress(IndexError):
            self.img.putpixel((x+1, y-1), color)
        with suppress(IndexError):
            self.img.putpixel((x+1, y+0), color)
        with suppress(IndexError):
            self.img.putpixel((x+1, y+1), color)
        with suppress(IndexError):
            self.img.putpixel((x+0, y+1), color)
        with suppress(IndexError):
            self.img.putpixel((x-1, y+1), color)
        with suppress(IndexError):
            self.img.putpixel((x-1, y+0), color)

    @property
    def data(self) -> Generator[Tuple[int, int, str], None, None]:
        off_x = floor(self.w / 2)
        off_y = floor(self.h / 2)
        for p in self.points:
            x = self.sec2pixel(-p[0] - self.center_ra_off, 'x') + off_x
            y = self.sec2pixel(-p[1] - self.center_de_off, 'y') + off_y
            if 0 <= x <= self.w - 1 and 0 <= y <= self.h - 1:
                yield x, y, p[2]
