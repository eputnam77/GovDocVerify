#!/usr/bin/env bash
# Ensure Semgrep is available
python3 -m pip install semgrep
# Determine next agent in the Codex workflow
set -euo pipefail

# Retrieve last commit message
LAST_COMMIT=$(git log -1 --pretty=%B)

# Look for ``ready-for:<agent>`` marker
if [[ "$LAST_COMMIT" =~ ready-for:([a-zA-Z0-9_-]+) ]]; then
  NEXT_AGENT="${BASH_REMATCH[1]}"
else
  NEXT_AGENT=""
fi

export NEXT_AGENT
echo "NEXT_AGENT=${NEXT_AGENT}"
