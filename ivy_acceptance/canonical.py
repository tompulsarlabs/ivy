"""Portable manifest identity; all functions are read-only."""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath


class InvalidManifest(ValueError):
    pass


def _validate_json(value):
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            _validate_json(item)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            _validate_json(item)
        return
    raise InvalidManifest("manifest must contain only finite JSON values and string keys")


def canonical_bytes(value):
    _validate_json(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidManifest(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise InvalidManifest(f"non-finite JSON value: {value}")

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          object_pairs_hook=unique, parse_constant=invalid_constant)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise InvalidManifest(str(exc)) from exc


def relative_path(value):
    if type(value) is not str or not value or "\\" in value or "\0" in value:
        raise InvalidManifest("expected a normalized relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value or value == ".":
        raise InvalidManifest(f"unsafe or non-normalized path: {value}")
    return path


def contained_path(root, value):
    rel = relative_path(value)
    root = Path(root).resolve(strict=True)
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise InvalidManifest("symlinks are not supported in scaffold inputs")
    if not path.exists():
        raise InvalidManifest(f"missing input: {value}")
    return path


def snapshot_tree(root):
    """Hash explicit input trees, rejecting links and case-insensitive path aliases.

    Operator-controlled local files only; this is not a hostile-filesystem sandbox.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise InvalidManifest("snapshot root must be a real directory")
    entries, names = [], set()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise InvalidManifest("symlinks are not supported in scaffold inputs")
        if path.is_dir():
            continue
        if not path.is_file():
            raise InvalidManifest("only regular input files are supported")
        name = path.relative_to(root).as_posix()
        relative_path(name)
        if name.casefold() in names:
            raise InvalidManifest("duplicate portable path")
        names.add(name.casefold())
        entries.append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "executable": bool(path.stat().st_mode & 0o111)})
    if not entries:
        raise InvalidManifest("input tree cannot be empty")
    return entries
