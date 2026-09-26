import struct
import _loader  # noqa: F401 — loads picimport as picimport_mod
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


class TiffSafetyAndHeaderRead(unittest.TestCase):
    """Corrupt RAW must not crash; big RAW must not be read whole."""

    def setUp(self):
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())

    def path(self, name: str, data: bytes) -> Path:
        p = self.tmp / name
        p.write_bytes(data)
        return p

    def test_ifd_claims_more_entries_than_present(self):
        """Regression: struct.error escaped read_capture_datetime.

        A truncated TIFF whose IFD claims 5 entries but contains none used
        to kill the whole import run — violating the documented
        "parsing never fails loudly".
        """
        data = (
            b"II*\x00"
            + struct.pack("<I", 8)
            + struct.pack("<H", 5)
            + struct.pack("<I", 0)
        )
        self.assertIsNone(read_capture_datetime(self.path("trunc.tif", data)))

    def test_large_tiff_reads_only_header(self):
        """Performance: 4 MiB of padding must not be read for dating.

        TIFF-based RAW (CR2/NEF/DNG) keeps date tags in the first IFD;
        reading the whole file made dry runs minutes-slow on slow readers.
        Guard: Path.read_bytes on a >256 KiB RAW must never happen.
        """
        from unittest import mock

        tiff = make_tiff({0x9003: "2026:09:20 12:00:00"})
        padded = tiff + b"\x00" * (4 * 1024 * 1024)
        p = self.path("big.cr2", padded)
        original = Path.read_bytes

        def fail_if_huge(inner):
            if inner.stat().st_size > 262144:
                raise AssertionError("whole-file read on RAW — header-only expected")
            return original(inner)

        with mock.patch.object(Path, "read_bytes", fail_if_huge):
            dt = read_capture_datetime(p)
        self.assertEqual(dt, datetime(2026, 9, 20, 12, 0))  # noqa: DTZ001


if __name__ == "__main__":
    unittest.main()
