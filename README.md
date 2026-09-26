# picimport

**One-command photo import for Linux.** Point it at a camera card (or any
folder of media) and it copies everything into local, date-organized folders —
nothing more, nothing less. Not affiliated with any camera vendor.

```
$ picimport -i /media/ian/SDCARD/DCIM
[1] ~/Pictures/Import/2026-08-22/DSC_0001.JPG
[2] ~/Pictures/Import/2026-08-22/DSC_0002.NEF
[3] ~/Pictures/Import/2026-08-15/DSC_0003.JPG
Copied 3 image(s), 0 video(s), Skipped 0, Failed 0
```

## Why this exists

Camera cards accumulate shots over days, and manual copying mixes them into
one folder or loses the capture date entirely. picimport reads each file's
EXIF capture time and files it under `YYYY-MM-DD`, so a week-long trip lands
in seven tidy folders. Re-inserting a card after a few extra shots imports
only the new ones.

Built for a terminal-first Linux workflow (and AI agents) where photo import
should be one boring, predictable command with zero dependencies.

## Install

Python 3.13 standard library only — no pip, no venv, no dependencies.

```bash
git clone https://github.com/obionar/picimport.git
cd picimport && ./install.sh
```

This installs the CLI to `~/.local/bin`. To also install the bundled
agent skill (`skill/picimport/SKILL.md`, AgentSkills-compatible), pass your
agent's skills dir explicitly: `./install.sh --skill-dir ~/.claude/skills`
— skills are never auto-installed into every agent found; each agent
integrates the skill itself when you ask it to. `--uninstall` removes
both. Manual CLI-only alternative:

```bash
cp picimport/picimport ~/.local/bin/
chmod +x ~/.local/bin/picimport
```

Any directory on `PATH` works; keep the file executable.

### Install as an agent skill

If you use an AI agent with shell access (Hermes, OpenClaw, Claude Code, …),
paste the repository URL into the agent chat and ask it to install the tool
as a skill:

> https://github.com/obionar/picimport — install this as a skill:
> copy the script to ~/.local/bin (chmod +x), read AGENTS.md and follow it.

The repository ships a ready-made agent-neutral skill at
`skill/picimport/SKILL.md`; the integrating agent installs it into its own
skills dir via `./install.sh --skill-dir <dir>`. `AGENTS.md` contains
everything the agent needs: command contract, output shape, and boundaries.

## Usage

```
picimport -i PATH       source directory to import from (required unless set in config)
picimport -p DIR        destination root for images (default: ~/Pictures/Import)
picimport -V DIR        destination root for videos (default: ~/Videos/Import)
picimport -S DIR        destination for screenshots (default: ~/Pictures/Screenshots)
picimport --config FILE alternative config file path
picimport -n            dry run: print planned copies, change nothing
picimport --progress    show [X/Y] progress counter
picimport --version     print version
```

### Configuration

Optional defaults live in `~/.config/picimport/config.toml` (respects
`$XDG_CONFIG_HOME`). Every key is optional; command-line flags always win.

```toml
# ~/.config/picimport/config.toml
source_dir = "~/Pictures/InstantUpload/Camera"   # lets you run bare `picimport`
pictures_dir = "~/Pictures/Import"
videos_dir = "~/Videos/Import"
```

### Typical workflow

1. Insert SD card, run `picimport -i /media/$USER/SDCARD/DCIM`.
2. Review the summary line.
3. Later, after a few more shots on the same card, run the same command again:
   previously imported files are skipped instantly, only new ones are copied.

### Progress indicator

For large imports, add `--progress` to show `[X/Y]` counters:

```
picimport -i /media/ian/SDCARD/DCIM --progress
[1/247] copying .../DSC_0001.JPG -> ~/Pictures/Import/2026-08-22/DSC_0001.JPG
[2/247] copying .../DSC_0002.NEF -> ~/Pictures/Import/2026-08-22/DSC_0002.NEF
...
```

## How it works

1. **Scan** — walks the source recursively, collecting recognized media:

   images `.jpg .jpeg .png .heic .heif .tif .tiff .cr2 .cr3 .nef .arw .orf .rw2 .raf .dng`
   · videos `.mp4 .mov .m4v .avi .mkv .webm .3gp .mts`

2. **Date resolution** — per file, in order:
   - EXIF `DateTimeOriginal` (tag `0x9003`)
   - EXIF `DateTimeDigitized` (tag `0x9004`)
   - EXIF `DateTime` (tag `0x0132`)
   - MP4/MOV `moov > mvhd > creation_time` (for `.mp4 .mov .m4v .3gp .mts`)
   - File modification time

   The built-in reader parses Exif APP1 segments inside JPEGs and direct
   TIFF structures (which covers CR2/NEF/ARW/ORF/RW2/DNG/TIFF). Files that
   cannot be parsed fall back to mtime; parsing never fails loudly.

3. **Target selection** — images under the pictures root, videos under the
   videos root, as `<root>/<YYYY-MM-DD>/<original name>`. Same name + same
   byte size already present → skip (re-import safe). Same name + different
   content → `<stem>_1<ext>`, `<stem>_2<ext>`, … (never overwrites).

4. **Copy + verify** — `shutil.copyfile`, then compare destination and source
   byte lengths. A mismatch removes the partial copy and counts as failed.

Exit codes: `0` on success (including dry run), `2` on bad input (source not
a directory / no source given).

## Limitations

- Duplicate detection is name+size against the target date folder only.
- HEIC/PNG rarely carry EXIF; those fall back to mtime.
- No move-only mode, no renaming scheme, no library management — by design.

## Tests

```bash
python3 -m unittest discover tests -v
```

Offline only — synthetic TIFF/JPEG fixtures, no live media required.

## License

GPL-3.0-only — see [LICENSE](LICENSE).
