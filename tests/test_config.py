import tempfile
import _loader  # noqa: F401 — loads picimport as picimport_mod
import unittest
from pathlib import Path

import tomllib
from picimport_mod import *
from picimport_mod import (
    DEFAULT_PICTURES_DIR,
    DEFAULT_VIDEOS_DIR,
    load_config,
    media_kind,
)


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, content: str) -> Path:
        p = self.tmp / "config.toml"
        p.write_text(content)
        return p

    def test_missing_file_returns_empty(self):
        self.assertEqual(load_config(self.tmp / "nope.toml"), {})

    def test_known_keys_loaded_and_expanded(self):
        cfg = load_config(
            self.write(
                'source_dir = "~/Card"\npictures_dir = "/data/pics"\nvideos_dir = "/data/vids"\n'
            )
        )
        self.assertEqual(cfg["source_dir"], Path.home() / "Card")
        self.assertEqual(cfg["pictures_dir"], Path("/data/pics"))
        self.assertEqual(cfg["videos_dir"], Path("/data/vids"))

    def test_unknown_and_bad_values_ignored(self):
        cfg = load_config(self.write('foo = 1\npictures_dir = 42\nvideos_dir = ""\n'))
        self.assertEqual(cfg, {})

    def test_malformed_toml_returns_empty(self):
        self.assertEqual(load_config(self.write("not [ valid toml")), {})

    def test_defaults_match_documented_paths(self):
        self.assertTrue(tomllib.loads('x = "t"'))  # tomllib available
        self.assertEqual(DEFAULT_PICTURES_DIR, Path.home() / "Pictures" / "Import")
        self.assertEqual(DEFAULT_VIDEOS_DIR, Path.home() / "Videos" / "Import")


class KindTest(unittest.TestCase):
    def test_images(self):
        for name in ("a.jpg", "b.CR3", "c.heic", "d.dng"):
            self.assertEqual(media_kind(Path(name)), "image")

    def test_videos(self):
        for name in ("a.mp4", "b.MOV", "c.m4v", "d.mkv"):
            self.assertEqual(media_kind(Path(name)), "video")

    def test_unknown_counts_as_image(self):
        self.assertEqual(media_kind(Path("x.xyz")), "image")


if __name__ == "__main__":
    unittest.main()
