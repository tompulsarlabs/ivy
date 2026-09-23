#!/usr/bin/env bash
# Thin launchd entry point — the scanner lives in local-wip.py.
# (launchd job points here; keep this path stable.)
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
exec python3 "$(dirname "$0")/local-wip.py" "$@"
