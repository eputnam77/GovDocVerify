#!/usr/bin/env python3
"""Minimal lint-staged runner for environments without Node.

Reads `lint-staged` config from `package.json` and applies commands to
staged files matching the configured globs.
"""
from __future__ import annotations

import fnmatch
import json
import shlex
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path.cwd()
    pkg_file = repo_root / "package.json"
    if not pkg_file.exists():
        return 0
    config = json.loads(pkg_file.read_text()).get("lint-staged", {})
    if not config:
        return 0

    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True,
        text=True,
        check=True,
    )
    files = result.stdout.strip().splitlines()

    for pattern, command in config.items():
        matched = [f for f in files if fnmatch.fnmatch(f, pattern)]
        if not matched:
            continue
        cmd = shlex.split(command) + matched
        res = subprocess.run(cmd, cwd=repo_root)
        if res.returncode != 0:
            return res.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
