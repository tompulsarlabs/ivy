"""Recompile the preview and pack only verified worker-visible bytes."""
import hashlib
import io
import tarfile
from pathlib import Path

from .canonical import InvalidManifest, contained_path, digest
from .planning import compile_plan


def materialize_preview(config, envelope, root, case_id, variant):
    """This authorizes a credential-free runtime probe ONLY, never an agent run.

    Operator-controlled input directories must remain stable while reading. Every
    byte copied is checked against its snapshot, even after plan recompilation.
    """
    if (set(envelope) != {"plan", "plan_sha256"}
            or digest(envelope["plan"]) != envelope["plan_sha256"]
            or compile_plan(config, root) != envelope):
        raise InvalidManifest("saved plan or current inputs changed")
    if variant not in ("baseline", "changed"):
        raise InvalidManifest("unknown variant")
    case = next((c for c in config["cases"] if c["id"] == case_id), None)
    if case is None:
        raise InvalidManifest("unknown case")
    record = next(c for c in envelope["plan"]["benchmark"]["cases"] if c["id"] == case_id)
    agent = envelope["plan"]["variants"][variant]
    files = {}
    trees = (("fixture", case["worker_dir"], record["worker_files"]),
             ("instructions", config["variants"][variant]["instructions_dir"], agent["agent_version"]["instruction_files"]))
    for prefix, directory, entries in trees:
        source = contained_path(root, directory)
        for item in entries:
            path = contained_path(source, item["path"])
            body = path.read_bytes()
            if (hashlib.sha256(body).hexdigest() != item["sha256"]
                    or bool(path.stat().st_mode & 0o111) != item["executable"]):
                raise InvalidManifest("input changed during materialization")
            files[f"{prefix}/{item['path']}"] = body
    binding = {"plan_sha256": envelope["plan_sha256"], "case_id": case_id, "variant": variant,
               "fixture_sha256": record["fixture_sha256"], "agent_version_sha256": agent["agent_version_sha256"]}
    return files, binding


def pack_worker(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        directories = {"worker"}
        for name in files:
            directories.update(str(p) for p in Path("worker", name).parents if str(p) != ".")
        for name in sorted(directories, key=lambda p: (p.count("/"), p)):
            entry = tarfile.TarInfo(name)
            entry.type, entry.mode = tarfile.DIRTYPE, 0o755
            archive.addfile(entry)
        for name, body in sorted(files.items()):
            from .canonical import relative_path
            relative_path(name)
            entry = tarfile.TarInfo("worker/" + name)
            entry.size, entry.mode = len(body), 0o444
            archive.addfile(entry, io.BytesIO(body))
    return buffer.getvalue()
