"""Render a native Paperclip SSH environment without reading private keys.

This prepares connection settings; it neither creates an account, opens SSH,
connects to a machine, nor launches an agent.
"""
import argparse
import base64
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
import uuid


def environment(*, host, username, workspace, secret_id, known_hosts, port=22, secret_version=1):
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", host) or ".." in host:
        raise ValueError("invalid_worker_host")
    try:
        address = ipaddress.ip_address(host)
        private = (address in ipaddress.ip_network("10.0.0.0/8")
                   or address in ipaddress.ip_network("172.16.0.0/12")
                   or address in ipaddress.ip_network("192.168.0.0/16")
                   or address in ipaddress.ip_network("100.64.0.0/10"))
    except ValueError:
        private = host.endswith(".ts.net")
    if not private:
        raise ValueError("worker_requires_private_network_address")
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", username) or username in {"root", "tom"}:
        raise ValueError("dedicated_worker_account_required")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("invalid_ssh_port")
    path = PurePosixPath(workspace)
    home = PurePosixPath("/Users") / username
    if (not path.is_absolute() or ".." in path.parts or not path.is_relative_to(home)
            or path == home or ".ssh" in path.parts or ".codex" in path.parts or ".claude" in path.parts):
        raise ValueError("dedicated_workspace_required")
    try:
        secret_id = str(uuid.UUID(secret_id))
    except (ValueError, AttributeError):
        raise ValueError("invalid_paperclip_secret_id") from None
    if type(secret_version) is not int or secret_version < 1:
        raise ValueError("pinned_secret_version_required")
    # Require a single explicit ed25519 host pin. No wildcard, TOFU or private key.
    fields = known_hosts.strip().split()
    target = host if port == 22 else f"[{host}]:{port}"
    if len(fields) != 3 or fields[0] != target or fields[1] != "ssh-ed25519":
        raise ValueError("exact_ed25519_host_pin_required")
    try:
        blob = base64.b64decode(fields[2], validate=True)
        if len(blob) != 51 or blob[:19] != b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20":
            raise ValueError()
    except ValueError:
        raise ValueError("invalid_ed25519_host_pin") from None
    return {"name": "Ivy Mac worker", "driver": "ssh", "config": {
        "host": host, "port": port, "username": username, "remoteWorkspacePath": str(path),
        "privateKey": None,
        "privateKeySecretRef": {"type": "secret_ref", "secretId": secret_id, "version": secret_version},
        "knownHosts": known_hosts.strip(), "strictHostKeyChecking": True}, "envVars": {}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("host", "username", "workspace", "secret-id", "known-hosts-file", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--secret-version", type=int, default=1)
    args = parser.parse_args()
    try:
        known_hosts = Path(args.known_hosts_file).read_text()
        result = environment(host=args.host, username=args.username, workspace=args.workspace,
                             secret_id=args.secret_id, known_hosts=known_hosts, port=args.port,
                             secret_version=args.secret_version)
        with Path(args.output).open("x") as output:
            output.write(json.dumps(result, indent=2) + "\n")
    except (ValueError, OSError) as exc:
        # Filesystem errors can contain paths. No key material or input values.
        print(json.dumps({"status": "refused", "reason": str(exc) if isinstance(exc, ValueError) else type(exc).__name__}))
        return 2
    print(json.dumps({"status": "prepared", "connected": False, "agent_started": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
