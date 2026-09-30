"""Fail closed before starting the private, board-only Paperclip deployment.

No network calls, secret values in output, model execution or database mutations.
The upstream entrypoint runs this as its unprivileged server user.
"""
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit


def validate_environment(env):
    errors = []
    required = {
        "PAPERCLIP_DEPLOYMENT_MODE": "authenticated",
        "PAPERCLIP_DEPLOYMENT_EXPOSURE": "public",
        "PAPERCLIP_HOME": "/paperclip",
        "HEARTBEAT_SCHEDULER_ENABLED": "false",
    }
    for key, value in required.items():
        if env.get(key) != value:
            errors.append("invalid_" + key.lower())
    origin = env.get("PAPERCLIP_AUTH_PUBLIC_BASE_URL", "")
    try:
        url = urlsplit(origin)
        valid = (url.scheme == "https" and url.hostname and not url.username
                 and not url.password and url.path in ("", "/")
                 and not url.query and not url.fragment and url.port in (None, 443))
        if not valid:
            raise ValueError()
        hosts = {x.strip().lower() for x in env.get("PAPERCLIP_ALLOWED_HOSTNAMES", "").split(",") if x.strip()}
        if url.hostname.lower() not in hosts or not hosts <= {url.hostname.lower(), "healthcheck.railway.app"}:
            errors.append("invalid_allowed_hostnames")
    except ValueError:
        errors.append("invalid_https_origin")
    for key in ("PAPERCLIP_PUBLIC_URL", "BETTER_AUTH_URL", "BETTER_AUTH_BASE_URL"):
        if env.get(key) and env[key].rstrip("/") != origin.rstrip("/"):
            errors.append("conflicting_auth_origin")
    secret = env.get("BETTER_AUTH_SECRET", "")
    if len(secret) < 32 or len(set(secret)) < 12:
        errors.append("missing_or_weak_auth_secret")
    try:
        key = base64.b64decode(env.get("PAPERCLIP_SECRETS_MASTER_KEY", ""), validate=True)
        if len(key) != 32 or len(set(key)) < 12:
            raise ValueError()
    except (ValueError, TypeError):
        errors.append("invalid_base64_master_key")
    try:
        db = urlsplit(env.get("DATABASE_URL", ""))
        if (db.scheme not in ("postgres", "postgresql") or not db.hostname
                or not db.username or not db.password or db.path in ("", "/")
                or db.fragment or db.port == 0):
            raise ValueError()
    except ValueError:
        errors.append("invalid_database_url")
    # This first release hosts a board, with no model credentials or workers.
    if any(env.get(key) for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                                    "GOOGLE_API_KEY", "OPENROUTER_API_KEY")):
        errors.append("model_credentials_not_allowed_in_board_release")
    return sorted(set(errors))


def check_storage(root):
    if not root.is_dir() or not os.path.ismount(root):
        return ["persistent_app_volume_missing"]
    try:
        with tempfile.TemporaryFile(dir=root) as probe:
            probe.write(b"ivy-storage-preflight\n")
            probe.flush()
            os.fsync(probe.fileno())
    except OSError:
        return ["persistent_app_volume_not_writable"]
    return []


def ensure_config(env, root):
    """Create the config needed by upstream owner/backup CLI commands once."""
    path = root / "instances/default/config.json"
    config = {
        "$meta": {"version": 1, "updatedAt": datetime.now(timezone.utc).isoformat(), "source": "configure"},
        "database": {"mode": "postgres", "connectionString": env["DATABASE_URL"]},
        "logging": {"mode": "file", "logDir": str(root / "instances/default/logs")},
        "server": {"deploymentMode": "authenticated", "exposure": "public", "bind": "custom",
                   "customBindHost": "0.0.0.0", "host": "0.0.0.0", "port": int(env.get("PORT", "3100")),
                   "allowedHostnames": [x.strip() for x in env["PAPERCLIP_ALLOWED_HOSTNAMES"].split(",")]},
        "auth": {"baseUrlMode": "explicit", "publicBaseUrl": env["PAPERCLIP_AUTH_PUBLIC_BASE_URL"],
                 "disableSignUp": env.get("PAPERCLIP_AUTH_DISABLE_SIGN_UP") == "true"},
        "telemetry": {"enabled": False}, "updates": {"checkEnabled": False},
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            existing = json.loads(path.read_text())
            if existing.get("database", {}).get("connectionString") != env["DATABASE_URL"]:
                return ["persisted_database_config_differs_from_environment"]
            return []
        with os.fdopen(fd, "w") as output:
            json.dump(config, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
    except (OSError, ValueError, AttributeError):
        return ["persistent_config_unavailable"]
    return []


def main():
    errors = validate_environment(os.environ)
    if not errors:
        errors.extend(check_storage(Path("/paperclip")))
    if not errors:
        errors.extend(ensure_config(os.environ, Path("/paperclip")))
    print(json.dumps({"ivy_preflight": "fail" if errors else "pass", "reasons": errors}), flush=True)
    if errors:
        return 2
    # The pinned board-mutation guard reads PUBLIC_URL, whereas Better Auth
    # reads AUTH_PUBLIC_BASE_URL. Both must use the same canonical origin when
    # a reverse proxy sends an internal Host header.
    os.environ["PAPERCLIP_PUBLIC_URL"] = os.environ["PAPERCLIP_AUTH_PUBLIC_BASE_URL"]
    # Fixed command from the pinned upstream image. No command supplied by a task.
    os.chdir("/app")
    os.execvp("node", ["node", "--import", "./server/node_modules/tsx/dist/loader.mjs", "server/dist/index.js"])


if __name__ == "__main__":
    sys.exit(main())
