---
name: picimport
description: Use when importing photos/videos from a card or folder into date-organized folders.
license: GPL-3.0-only
tool-version: 1.1.0
---

# picimport — EXIF-dated media import from the terminal

One-command media import for Linux: copies images into
`~/Pictures/Import/<YYYY-MM-DD>/` and videos into
`~/Videos/Import/<YYYY-MM-DD>/` by EXIF capture date. Single-file Python 3.13
(stdlib only), no install beyond copy-to-PATH. Copy-only by default — it
deletes from the source only after byte-length-verified copy AND explicit
confirmation.

## When to use

- The user inserted a camera card / wants photos off a folder, organized by
  capture date.
- Re-importing a partially imported card: already-copied files are skipped
  automatically (name+size dedupe), so re-running is always safe.

## Command contract

```
picimport -i PATH [-p PICTURES_DIR] [-V VIDEOS_DIR] [--config FILE] [-n] [-y]
```

- `-i` (or `source_dir` in config) is required; missing source → exit 2.
- `-n` dry run: prints planned copies, changes nothing, exit 0.
- `-y` auto-confirms post-copy deletion. **Never pass `-y` unless the user
  explicitly asked for source deletion.**
- Exit codes: `0` success (incl. dry run) · `2` bad input.
- Progress goes to stdout, errors/warnings to stderr, one summary line at the
  end: `Copied X image(s), Y video(s), Skipped N, Failed M, Deleted K`.

## Semantics an agent must respect

- **Deletion safety is the hard rule**: only files that were copied and
  byte-length-verified are ever eligible for deletion; failures are never
  deleted. The tool enforces this itself — do not work around it.
- Re-importing the same card is safe and quiet: same name+size in the target
  date folder → skipped.
- Date folders come from EXIF DateTimeOriginal (fallback chain to mtime);
  never sort or rename afterwards — the tool's layout is the contract.
- Config: `~/.config/picimport/config.toml` (`source_dir`, `pictures_dir`,
  `videos_dir`); CLI flags always win. Malformed config → warning + defaults.
- The delete prompt reads stdin; in a non-interactive context it answers "no"
  (safe default). Use `-y` only with explicit user intent.

## Safety boundaries (hard rules)

- Never rewrite, rename, or "clean up" files inside the Import trees without
  the user asking — dedupe depends on the layout staying stable.
- Never import INTO the source tree itself (source and destination roots
  must differ).
- The tool never touches files it does not recognize (unknown extensions are
  ignored, never deleted).

## Version check

This skill documents `picimport` **1.0.0** (`tool-version` above). Before
relying on the command contract, run `picimport --version`:

- **Match** → proceed.
- **Mismatch** → skill and tool have drifted apart; the command contract
  above may be wrong. Refresh both from the source before continuing:
  ```bash
  git -C <your-clone-dir> pull && ./install.sh
  # no clone yet? git clone https://github.com/obionar/picimport.git && cd picimport && ./install.sh
  ```
  Then re-run `--version` and reload this skill if it changed. Do not guess
  how an unknown version behaves — old flags may be gone or renamed.

## Install

```bash
git clone https://github.com/obionar/picimport.git
cd picimport && ./install.sh --skill-dir ~/.your-agent/skills
```

`./install.sh` alone installs only the CLI; the skill goes into ONE
explicitly passed skills dir — the agent integrating this tool passes its
own (e.g. `~/.claude/skills`, `~/.hermes/skills`).

No API keys, no configuration needed (config.toml is optional).
