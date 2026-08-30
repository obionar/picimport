import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "picimport"

if "picimport_mod" not in sys.modules:  # idempotent loader
    _loader = SourceFileLoader("picimport_mod", str(SCRIPT))
    _spec = importlib.util.spec_from_loader("picimport_mod", _loader)
    picimport = importlib.util.module_from_spec(_spec)
    sys.modules["picimport_mod"] = picimport
    _loader.exec_module(picimport)
import struct
import unittest
from datetime import datetime
from pathlib import Path

from picimport_mod import *
from picimport_mod import read_capture_datetime


def make_tiff(entries: dict[int, str]) -> bytes:
    """Build a minimal little-endian TIFF IFD0 with ASCII date entries."""
    tags = sorted(entries)
    n = len(tags)
    ifd_offset = 8
    data_start = ifd_offset + 2 + 12 * n + 4

    ifd = struct.pack("<H", n)
    body = b""
    for tag in tags:
        value = entries[tag].encode("ascii") + b"\x00"
        count = len(value)
        if count <= 4:
            ifd += struct.pack("<HHI", tag, 2, count) + value.ljust(4, b"\x00")
        else:
            ifd += struct.pack("<HHII", tag, 2, count, data_start + len(body))
            body += value + (b"\x00" if count % 2 else b"")
    ifd += struct.pack("<I", 0)  # no next IFD
    return b"II" + struct.pack("<HI", 42, ifd_offset) + ifd + body


def make_jpeg(tiff: bytes) -> bytes:
    payload = b"Exif\x00\x00" + tiff
    seg = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    return b"\xff\xd8" + seg + b"\xff\xd9"


class ExifTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())

    def path(self, name: str, data: bytes) -> Path:
        p = self.tmp / name
        p.write_bytes(data)
        return p

    def test_tiff_datetime_original(self):
        tiff = make_tiff({0x0132: "2000:01:01 00:00:00", 0x9003: "2026:08:22 10:30:00"})
        dt = read_capture_datetime(self.path("a.nef", tiff))
        self.assertEqual(dt, datetime(2026, 8, 22, 10, 30))  # noqa: DTZ001

    def test_tiff_fallback_datetime(self):
        tiff = make_tiff({0x0132: "2021:03:04 05:06:07"})
        dt = read_capture_datetime(self.path("b.cr2", tiff))
        self.assertEqual(dt, datetime(2021, 3, 4, 5, 6, 7))  # noqa: DTZ001

    def test_jpeg_exif_segment(self):
        tiff = make_tiff({0x9003: "2026-08-22 10:30:00"})
        dt = read_capture_datetime(self.path("c.jpg", make_jpeg(tiff)))
        self.assertEqual(dt, datetime(2026, 8, 22, 10, 30))  # noqa: DTZ001

    def test_no_exif_returns_none(self):
        self.assertIsNone(
            read_capture_datetime(self.path("d.jpg", b"\xff\xd8\xff\xd9"))
        )

    def test_non_image_returns_none(self):
        self.assertIsNone(read_capture_datetime(self.path("e.txt", b"hello")))

    def test_garbage_tiff_is_safe(self):
        self.assertIsNone(read_capture_datetime(self.path("f.tif", b"II*\x00garbage!")))


if __name__ == "__main__":
    unittest.main()
