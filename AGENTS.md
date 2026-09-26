# AGENTS.md — picimport integration guide for AI agents

This file teaches a coding/automation agent (Hermes, OpenClaw, Claude Code,
etc.) how to use this tool correctly. Keep it in prompts as-is.

## What this tool is

One-command media import for Linux: copies images into
`~/Pictures/Import/<YYYY-MM-DD>/` and videos into `~/Videos/Import/<YYYY-MM-DD>/`
by EXIF capture date. Single-file Python 3.13 (stdlib only), no install
beyond copy-to-PATH. Copy-only — source files are always preserved.

## Command contract

```
picimport -i PATH [-p PICTURES_DIR] [-V VIDEOS_DIR] [-S SCREENSHOTS_DIR] [--config FILE] [-n] [--progress]
```

- `-i` (or `source_dir` in config) is required; missing source → exit 2.
- `-n` dry run: prints planned copies, changes nothing, exit 0.
- `--progress` show sequential counter during import.
- Exit codes: `0` success (incl. dry run) · `2` bad input.
- Progress goes to stdout, errors/warnings to stderr, one summary line at the
  end: `Copied X image(s), Y video(s), Skipped N, Failed M`.

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

This repository ships a ready-made, agent-neutral skill at
`skill/picimport/SKILL.md` (AgentSkills-compatible SKILL.md with YAML
frontmatter — the same format Claude Code, OpenCode, OpenClaw, and Hermes
load). `./install.sh` installs ONLY the CLI. Skills are never sprayed into
every agent on the machine: when a user asks THIS agent to integrate the
tool, the agent runs
`./install.sh --skill-dir <its-own-skills-dir>` — one explicit target,
chosen by the agent that owns it, at the moment its user asks.

## Maintenance

- Tests: `python3 -m unittest discover tests` (synthetic TIFF/JPEG fixtures).
- After behavior changes: keep the summary-line format stable — scripts and
  agents parse it.
