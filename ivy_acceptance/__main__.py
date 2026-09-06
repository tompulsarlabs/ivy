"""Preview planning and explicit credential-free runtime probes."""
import argparse
import json
import sys
from pathlib import Path
from .canonical import InvalidManifest, read_json
from .planning import compile_plan
from .budget import BudgetBlocked
from .probe_cli import add_commands, run_command, command_exit
import subprocess


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="hash inputs and print a plan; never execute")
    plan.add_argument("config", type=Path)
    plan.add_argument("--root", type=Path, default=Path.cwd(), help="root of explicitly referenced inputs")
    add_commands(sub)
    args = parser.parse_args(argv)
    try:
        result = (compile_plan(read_json(args.config), args.root) if args.command == "plan" else run_command(args))
    except (InvalidManifest, BudgetBlocked, OSError, UnicodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc), "execution_started": False if args.command == "plan" else "inspect_persisted_reservation"}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return command_exit(result)


if __name__ == "__main__":
    raise SystemExit(main())
