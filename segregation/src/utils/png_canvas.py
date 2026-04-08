"""Creates simple PNG images without external plotting libraries for local report generation."""

import struct
import zlib


class PngCanvas:
    def __init__(self, width: int, height: int, background=(255, 255, 255)):
        self.width = width
        self.height = height
        self.pixels = [
            [list(background) for _ in range(width)]
            for _ in range(height)
        ]

    def fill_rect(self, x: int, y: int, width: int, height: int, color: tuple[int, int, int]):
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(self.width, x + width)
        y_end = min(self.height, y + height)

        for row in range(y_start, y_end):
            for col in range(x_start, x_end):
                self.pixels[row][col] = [color[0], color[1], color[2]]

    def draw_horizontal_line(self, x: int, y: int, length: int, color: tuple[int, int, int]):
        self.fill_rect(x, y, length, 1, color)

    def draw_vertical_line(self, x: int, y: int, length: int, color: tuple[int, int, int]):
        self.fill_rect(x, y, 1, length, color)

    def save(self, path: str):
        raw_rows = []
        for row in self.pixels:
            raw_rows.append(b"\x00" + bytes(channel for pixel in row for channel in pixel))

        raw_data = b"".join(raw_rows)
        compressed = zlib.compress(raw_data)

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (
                struct.pack("!I", len(data))
                + tag
                + data
                + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        png = [
            b"\x89PNG\r\n\x1a\n",
            chunk(
                b"IHDR",
                struct.pack("!IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0),
            ),
            chunk(b"IDAT", compressed),
            chunk(b"IEND", b""),
        ]

        with open(path, "wb") as output_file:
            output_file.write(b"".join(png))
