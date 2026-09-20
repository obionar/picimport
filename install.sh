#!/bin/sh
# install.sh — install picimport (CLI + agent skill)
#
# Installs:
#   1. The single-file CLI into ~/.local/bin (override: --bin-dir DIR)
#   2. The agent skill into ONE explicitly passed skills dir
#      (--skill-dir DIR) — owned by the agent integrating this tool
#
# Supported agents (auto-detected only for --uninstall; the directory is
# created only if the agent's config/state directory already exists):
#   Claude Code   ~/.claude/skills
#   OpenCode      ~/.config/opencode/skills
#   OpenClaw      ~/.openclaw/skills
#   AgentSkills   ~/.agents/skills   (cross-agent standard location)
#   Hermes        ~/.hermes/skills
#
# The skill format (SKILL.md with YAML frontmatter in a named folder) is the
# same AgentSkills-compatible format for all of the above.
#
# Usage:
#   ./install.sh                  # install the CLI only (default)
#   ./install.sh --skill-dir DIR  # install the skill into one agent's skills dir
#   ./install.sh --uninstall      # remove CLI + skill from standard agent dirs
#                                  (custom --skill-dir copies are not tracked)
#
# License: GPL-3.0-only — same as the repository and the CLI.

set -eu

TOOL_NAME="picimport"
REPO_URL="https://github.com/obionar/picimport"

CLI_ONLY=0
SKILL_ONLY=0
UNINSTALL=0
BIN_DIR="${HOME}/.local/bin"
SKILL_DIRS=""

usage() {
    sed -n '2,31p' "$0" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --cli-only)   CLI_ONLY=1 ;;
        --skill-only) SKILL_ONLY=1 ;;
        --uninstall)  UNINSTALL=1 ;;
        --bin-dir)    [ $# -ge 2 ] || usage 1; BIN_DIR="$2"; shift ;;
        --skill-dir)  [ $# -ge 2 ] || usage 1; SKILL_DIRS="$SKILL_DIRS $2"; shift ;;
        -h|--help)    usage 0 ;;
        *)            echo "unknown option: $1" >&2; usage 1 ;;
    esac
    shift
done

# --- Locate the repo root (this script's directory) -----------------------
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CLI_SRC="${REPO_ROOT}/${TOOL_NAME}"
SKILL_SRC="${REPO_ROOT}/skill/${TOOL_NAME}"

[ -x "$CLI_SRC" ] || { echo "error: ${CLI_SRC} not found or not executable" >&2; exit 1; }
[ -f "${SKILL_SRC}/SKILL.md" ] || { echo "error: ${SKILL_SRC}/SKILL.md not found" >&2; exit 1; }

if [ "$UNINSTALL" = 1 ]; then
    rm -f "${BIN_DIR}/${TOOL_NAME}"
    for d in \
        "${HOME}/.claude/skills/${TOOL_NAME}" \
        "${HOME}/.config/opencode/skills/${TOOL_NAME}" \
        "${HOME}/.openclaw/skills/${TOOL_NAME}" \
        "${HOME}/.agents/skills/${TOOL_NAME}" \
        "${HOME}/.hermes/skills/${TOOL_NAME}"; do
        [ -d "$d" ] && rm -rf "$d" && echo "removed skill: $d"
    done
    echo "uninstalled ${TOOL_NAME}"
    exit 0
fi

# --- 1. CLI ----------------------------------------------------------------
if [ "$SKILL_ONLY" = 0 ]; then
    mkdir -p "$BIN_DIR"
    install -m 0755 "$CLI_SRC" "${BIN_DIR}/${TOOL_NAME}"
    echo "installed CLI: ${BIN_DIR}/${TOOL_NAME}"
    case ":${PATH}:" in
        *":${BIN_DIR}:"*) ;;
        *) echo "note: ${BIN_DIR} is not on PATH" ;;
    esac
fi

# --- 2. Skill (explicit, per agent — never sprayed) -------------------------
if [ "$CLI_ONLY" = 0 ]; then
    if [ -z "$SKILL_DIRS" ]; then
        echo "skill not installed: pass the agent's skills dir explicitly, e.g."
        echo "  ./install.sh --skill-dir ~/.claude/skills"
        echo "Each agent installs this skill into its own dir when its user asks."
    else
        for d in $SKILL_DIRS; do
            dest="${d}/${TOOL_NAME}"
            rm -rf "$dest"
            mkdir -p "$d"
            cp -R "$SKILL_SRC" "$dest"
            echo "installed skill: $dest"
        done
    fi
fi

echo "done. Verify: ${TOOL_NAME} --version"
