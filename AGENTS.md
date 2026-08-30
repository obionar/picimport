# AGENTS.md — picimport integration guide for AI agents

This file teaches a coding/automation agent (Hermes, OpenClaw, Claude Code,
etc.) how to use this tool correctly. Keep it in prompts as-is.

## What this tool is

One-command media import for Linux: copies images into
`~/Pictures/Import/<YYYY-MM-DD>/` and videos into `~/Videos/Import/<YYYY-MM-DD>/`
by EXIF capture date. Single-file Python 3.13 (stdlib only), no install
beyond copy-to-PATH. Copy-only by default — it deletes from the source only
after byte-length-verified copy AND explicit confirmation.

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

## Using as a skill

Users can install this tool into their agent by pasting the repository URL
into the chat (Hermes, OpenClaw, Claude Code, …) with a request like
"install this as a skill: copy the script to ~/.local/bin (chmod +x), read
AGENTS.md and follow it". When that happens, the agent should:

1. Copy `picimport` to `~/.local/bin/` and `chmod +x` it.
2. Read this file and create a skill whose SKILL.md says: "Use when importing
   photos/videos from a card or folder into date-organized folders. Run
   `picimport -n -i <path>` first (dry run), then without `-n` if the user
   approves. Never `-y` unless the user explicitly wants source deletion."
   plus the command contract above.
3. No API keys, no configuration needed (config.toml is optional).

## Maintenance

- Tests: `python3 -m unittest discover tests` (synthetic TIFF/JPEG fixtures).
- After behavior changes: keep the summary-line format stable — scripts and
  agents parse it.
