#!/usr/bin/env python3
"""PreToolUse hook: let Claude's file tools write only to the allowed locations.

Covers Write, Edit, MultiEdit and NotebookEdit. Shell commands are restricted
separately by the Bash sandbox in .claude/settings.json.
Exit code 2 blocks the tool call; the message on stderr is shown to Claude.
"""
import json
import os
import re
import sys

DIET = "/Users/lisa/Documents/GitHub/gen2-longit/diet_log_analyses"

# Project locations Claude may write to.
ALLOWED_DIRS = [f"{DIET}/scripts", f"{DIET}/figures"]
ALLOWED_FILES = [f"{DIET}/PROGRESS.md"]

# Claude Code's own working files, outside the project: session scratchpad,
# auto memory and plan files.
ALLOWED_PATTERNS = [
    r"^/private/tmp/claude-\d+/",
    r"^/Users/lisa/\.claude/projects/[^/]+/memory/",
    r"^/Users/lisa/\.claude/plans/",
]


def allowed(path: str) -> bool:
    real = os.path.realpath(path)
    if real in [os.path.realpath(f) for f in ALLOWED_FILES]:
        return True
    for d in ALLOWED_DIRS:
        d = os.path.realpath(d)
        if real == d or real.startswith(d + os.sep):
            return True
    return any(re.match(p, real) for p in ALLOWED_PATTERNS)


def main() -> int:
    data = json.load(sys.stdin)
    tool_input = data.get("tool_input", {})
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not path:
        return 0
    if allowed(path):
        return 0
    print(
        f"Blocked by restrict_writes hook: {path} is outside the folders Claude may "
        f"write to (diet_log_analyses/scripts/, diet_log_analyses/figures/, "
        f"diet_log_analyses/PROGRESS.md). Do not work around this: tell the user "
        f"what you wanted to write and why.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
