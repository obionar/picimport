import tempfile
import _loader  # noqa: F401 — loads picimport as picimport_mod
import unittest
from datetime import datetime
from pathlib import Path

from picimport_mod import *
from picimport_mod import import_photos, resolve_target


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(self._cleanup)
        self.src = self.tmp / "card"
        self.pics = self.tmp / "dest" / "pictures"
        self.vids = self.tmp / "dest" / "videos"

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def touch(self, dirpath: Path, name: str, content: bytes) -> Path:
        dirpath.mkdir(parents=True, exist_ok=True)
        p = dirpath / name
        p.write_bytes(content)
        return p

    # resolve_target ------------------------------------------------------

    def test_resolve_free_name(self):
        src = self.touch(self.src, "IMG_1.jpg", b"a")
        target = resolve_target(self.pics / "2026-08-22", src)
        self.assertEqual(target, self.pics / "2026-08-22" / "IMG_1.jpg")

    def test_resolve_same_size_skips(self):
        dest_dir = self.pics / "2026-08-22"
        self.touch(dest_dir, "IMG_1.jpg", b"same-content!")
        src = self.touch(self.src, "IMG_1.jpg", b"same-content!")
        self.assertIsNone(resolve_target(dest_dir, src))

    def test_resolve_different_content_gets_suffix(self):
        dest_dir = self.pics / "2026-08-22"
        self.touch(dest_dir, "IMG_1.jpg", b"original")
        src = self.touch(self.src, "IMG_1.jpg", b"different")
        target = resolve_target(dest_dir, src)
        self.assertEqual(target, dest_dir / "IMG_1_1.jpg")

    def test_resolve_suffix_increments(self):
        dest_dir = self.pics / "2026-08-22"
        self.touch(dest_dir, "IMG_1.jpg", b"one")
        self.touch(dest_dir, "IMG_1_1.jpg", b"two")
        src = self.touch(self.src, "IMG_1.jpg", b"three")
        target = resolve_target(dest_dir, src)
        self.assertEqual(target, dest_dir / "IMG_1_2.jpg")

    def test_resolve_no_extension(self):
        dest_dir = self.pics / "2026-08-22"
        self.touch(dest_dir, "noext", b"x" * 5)
        src = self.touch(self.src, "noext", b"y" * 3)
        self.assertEqual(resolve_target(dest_dir, src), dest_dir / "noext_1")

    # end-to-end ----------------------------------------------------------

    def test_import_copies_and_skips_on_second_run(self):
        self.touch(self.src, "IMG_A.jpg", b"A" * 10)
        self.touch(self.src, "IMG_B.NEF", b"B" * 20)

        rc = import_photos(self.src, self.pics, self.vids)
        self.assertEqual(rc, 0)
        day = datetime.now().strftime("%Y-%m-%d")  # noqa: DTZ005 — naive local time is the tool's contract
        copied_dir = self.pics / day
        self.assertTrue((copied_dir / "IMG_A.jpg").is_file())
        self.assertTrue((copied_dir / "IMG_B.NEF").is_file())

        rc = import_photos(self.src, self.pics, self.vids)  # same card re-inserted
        self.assertEqual(rc, 0)
        self.assertFalse((copied_dir / "IMG_A_1.jpg").exists())

    def test_import_dry_run_touches_nothing(self):
        self.touch(self.src, "IMG_A.jpg", b"data")
        rc = import_photos(self.src, self.pics, self.vids, dry_run=True)
        self.assertEqual(rc, 0)
        self.assertFalse(self.pics.exists())

    def test_import_nonexistent_source_fails(self):
        rc = import_photos(self.tmp / "missing", self.pics, self.vids)
        self.assertEqual(rc, 2)

    def test_import_ignores_unknown_extensions(self):
        self.touch(self.src, "notes.txt", b"text")
        self.touch(self.src, "clip.mov", b"video")
        rc = import_photos(self.src, self.pics, self.vids)
        self.assertEqual(rc, 0)
        self.assertFalse(any(self.pics.rglob("*")))

    def test_import_delete_after_copy(self):
        self.touch(self.src, "IMG_A.jpg", b"A" * 10)
        rc = import_photos(self.src, self.pics, self.vids, assume_yes=True)
        self.assertEqual(rc, 0)
        self.assertFalse((self.src / "IMG_A.jpg").exists())
        self.assertTrue(any(self.pics.rglob("IMG_A.jpg")))

    def test_videos_route_to_videos_dir(self):
        self.touch(self.src, "VID_1.mp4", b"V" * 30)
        self.touch(self.src, "VID_2.MOV", b"W" * 40)
        rc = import_photos(self.src, self.pics, self.vids)
        self.assertEqual(rc, 0)
        day = datetime.now().strftime("%Y-%m-%d")  # noqa: DTZ005
        self.assertTrue((self.vids / day / "VID_1.mp4").is_file())
        self.assertTrue((self.vids / day / "VID_2.MOV").is_file())
        self.assertFalse(any(self.pics.rglob("*")))

    def test_mixed_media_routes_separately(self):
        self.touch(self.src, "IMG_A.jpg", b"A" * 10)
        self.touch(self.src, "VID_B.mp4", b"B" * 20)
        rc = import_photos(self.src, self.pics, self.vids)
        self.assertEqual(rc, 0)
        day = datetime.now().strftime("%Y-%m-%d")  # noqa: DTZ005
        self.assertTrue((self.pics / day / "IMG_A.jpg").is_file())
        self.assertTrue((self.vids / day / "VID_B.mp4").is_file())

    def test_video_dedupe_and_skip_on_second_run(self):
        self.touch(self.src, "VID_1.mp4", b"V" * 30)
        import_photos(self.src, self.pics, self.vids)
        rc = import_photos(self.src, self.pics, self.vids)  # re-inserted card
        self.assertEqual(rc, 0)
        self.assertEqual(sum(1 for p in self.vids.rglob("*") if p.is_file()), 1)

    def test_dry_run_reports_counts_and_copies_nothing(self):
        import tempfile
        from pathlib import Path

        tmp = Path(tempfile.mkdtemp())
        src = tmp / "src"
        pics = tmp / "pics"
        vids = tmp / "vids"
        src.mkdir()
        (src / "IMG_A.jpg").write_bytes(b"jpgdata")
        (src / "VID_1.mp4").write_bytes(b"viddata")
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = import_photos(src, pics, vids, dry_run=True)
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("would be copied", out)
        self.assertIn("1 image(s), 1 video(s) would be copied", out)
        self.assertFalse(pics.exists())
        self.assertFalse(vids.exists())

    def test_import_refuses_dest_inside_source(self):
        self.src.mkdir(parents=True)
        dest = self.src / "nested"
        dest.mkdir()
        rc = import_photos(self.src, dest, dest)
        self.assertEqual(rc, 2)

    def test_import_refuses_dest_is_source(self):
        rc = import_photos(self.src, self.src, self.src)
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
