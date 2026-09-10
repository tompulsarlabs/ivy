"""Bounded, strict readers for operator-selected offline evidence."""
import hashlib
import json
import math
from pathlib import Path
from .canonical import InvalidManifest, digest, relative_path

MAX_FILE = 4 * 1024 * 1024


class EvidenceError(InvalidManifest):
    """A stable public reason code; never embed raw evidence or host paths."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def finite_number(value):
    return (type(value) is int and value >= 0) or (type(value) is float and math.isfinite(value) and value >= 0)


def strict_json(data):
    try:
        text = data.decode('utf-8') if isinstance(data, bytes) else data
        depth, quoted, escaped = 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in '[{':
                depth += 1
                if depth > 16:
                    raise EvidenceError('json_depth_limit')
            elif char in ']}':
                depth -= 1
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise EvidenceError('duplicate_json_key')
                result[key] = value
            return result
        def invalid(value):
            raise EvidenceError('nonfinite_json')
        result = json.loads(text, object_pairs_hook=unique, parse_constant=invalid)
        def check(value):
            if type(value) is float and not math.isfinite(value):
                raise EvidenceError('nonfinite_json')
            if type(value) is dict:
                for item in value.values():
                    check(item)
            elif type(value) is list:
                for item in value:
                    check(item)
        check(result)
        return result
    except EvidenceError:
        raise
    except (ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise EvidenceError('invalid_json') from exc


def read_bytes(path, limit=MAX_FILE):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise EvidenceError('missing_or_nonregular_artifact')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise EvidenceError('artifact_size_limit')
    return data


def read_json_file(path):
    return strict_json(read_bytes(path))


def record_bytes(data):
    envelope = strict_json(data)
    if (type(envelope) is not dict or set(envelope) != {'record', 'sha256'}
            or digest(envelope['record']) != envelope['sha256']):
        raise EvidenceError('record_integrity_mismatch')
    if type(envelope['record']) is not dict:
        raise EvidenceError('record_shape_invalid')
    return envelope['record']


def artifact_name(name):
    try:
        relative_path(name)
    except InvalidManifest as exc:
        raise EvidenceError('artifact_path_invalid') from exc
    if '/' in name:
        raise EvidenceError('artifact_path_invalid')
    return name
