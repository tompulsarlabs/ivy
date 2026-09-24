#!/usr/bin/env bash
# Install the reviewed scanner from its stable main checkout, not a temp branch.
set -euo pipefail
LABEL="ai.tomgreen.ivy-wip"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$REPO_DIR/setup/$LABEL.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

case "${1:-}" in
  install)
    if [ "$(git -C "$REPO_DIR" branch --show-current)" != main ]; then
      echo "Install from the stable main checkout after the scanner change is reviewed and merged." >&2
      exit 1
    fi
    if ! git -C "$REPO_DIR" diff --quiet HEAD -- scripts/local-wip.py scripts/local-wip.sh setup/install-wip-scanner.sh setup/ai.tomgreen.ivy-wip.plist; then
      echo "Scanner installation files have uncommitted changes; install the reviewed version." >&2
      exit 1
    fi
    mkdir -p "$(dirname "$PLIST_DST")"
    python3 - "$PLIST_SRC" "$PLIST_DST" "$REPO_DIR" <<'PY'
import pathlib, plistlib, sys
source, target, repo = map(pathlib.Path, sys.argv[1:])
data = plistlib.loads(source.read_bytes())
data['ProgramArguments'] = ['/bin/bash', str(repo / 'scripts/local-wip.sh')]
data['EnvironmentVariables'] = {'IVY_DIR': str(repo)}
target.write_bytes(plistlib.dumps(data))
PY
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$PLIST_DST"
    echo "Scanner loaded for 08:45 and 17:45 local time. No scan has been started by this installer."
    echo "Preview: IVY_DIR=\"$REPO_DIR\" bash \"$REPO_DIR/scripts/local-wip.sh\" --dry-run"
    ;;
  status)
    if ! launchctl print "$DOMAIN/$LABEL"; then
      echo "Scanner is not loaded. Install the reviewed scanner from main." >&2
      exit 1
    fi
    ;;
  uninstall)
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    rm -f "$PLIST_DST"
    echo "Scanner unloaded. Published snapshots are unchanged."
    ;;
  *) echo "usage: bash $0 install|status|uninstall" >&2; exit 1 ;;
esac
