"""Offline fixed-program assessment; it cannot award agent benchmark acceptance."""
import base64
import binascii
import re
from pathlib import Path
from .canonical import digest, relative_path
from .evidence_io import (EvidenceError, artifact_name, finite_number, read_bytes,
                          record_bytes, sha, strict_json)

PROGRAM_SHA256 = 'ff5d328717984c218110e0815d2bda951321983a853140da119b8c5e352fdd4e'
POLICY = {'schema_version': 1, 'id': 'fixed-filesystem-probe-v1',
          'program_sha256': PROGRAM_SHA256, 'normalization': 'recorded-visible-files-v1',
          'rules_version': 1, 'write_results': ['OSError', 'FileNotFoundError']}
POLICY_SHA256 = digest(POLICY)
EXPECTATIONS = {'completion': 'completed', 'cancellation': 'canceled', 'deadline': 'timed_out'}
HASH = re.compile(r'[0-9a-f]{64}')


def aggregate(states):
    states = list(states)
    return 'fail' if 'fail' in states else 'unverified' if not states or 'unverified' in states else 'pass'


def load_bundle(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise EvidenceError('missing_or_nonregular_directory')
    raw = read_bytes(directory / 'receipt.json')
    receipt = record_bytes(raw)
    if (type(receipt.get('schema_version')) is not int or receipt['schema_version'] != 1
            or receipt.get('evidence_kind') != 'infrastructure_probe_not_model_evaluation'):
        raise EvidenceError('unsupported_receipt')
    stop_name = artifact_name(receipt.get('stop_evidence'))
    required = {'preparation.json', 'prepared.json', 'image-input.json', 'image-build.json', 'events.jsonl', stop_name}
    bindings = receipt.get('artifact_sha256')
    if type(bindings) is not dict or set(bindings) != required:
        raise EvidenceError('incomplete_artifact_bindings')
    contents, records = {}, {}
    for name in sorted(required):
        data = read_bytes(directory / name)
        if type(bindings[name]) is not str or not HASH.fullmatch(bindings[name]) or sha(data) != bindings[name]:
            raise EvidenceError('artifact_integrity_mismatch')
        contents[name] = data
        if name != 'events.jsonl':
            records[name] = record_bytes(data)
    if receipt.get('capture_sha256') != bindings['events.jsonl']:
        raise EvidenceError('capture_binding_mismatch')
    return receipt, records, contents['events.jsonl'], sha(raw)


def decode_capture(raw):
    rows, issues, channels, total = [], [], {'stdout': bytearray(), 'stderr': bytearray()}, 0
    last_time = 0
    shapes = {'start_requested': {'runtime_id'}, 'worker_stream': {'channel', 'data_base64'},
              'stream_closed': {'exit_code'}, 'stop_requested': {'reason'}}
    for index, line in enumerate(raw.splitlines(keepends=True), 1):
        try:
            if index > 16384 or len(line) > 131072:
                raise EvidenceError('supervisor_record_limit')
            if not line.endswith(b'\n'):
                raise EvidenceError('partial_supervisor_line')
            row = strict_json(line)
            if type(row) is not dict or type(row.get('kind')) is not str or row.get('kind') not in shapes:
                raise EvidenceError('unsupported_supervisor_event')
            if set(row) != {'kind', 'sequence', 'supervisor_elapsed_seconds'} | shapes[row['kind']]:
                raise EvidenceError('supervisor_event_shape')
            if type(row['sequence']) is not int or row['sequence'] != index:
                raise EvidenceError('supervisor_sequence_invalid')
            elapsed = row['supervisor_elapsed_seconds']
            if not finite_number(elapsed) or elapsed < last_time:
                raise EvidenceError('supervisor_time_invalid')
            last_time = elapsed
            if row['kind'] == 'worker_stream':
                if type(row['channel']) is not str or row['channel'] not in channels or type(row['data_base64']) is not str:
                    raise EvidenceError('worker_stream_shape')
                try:
                    chunk = base64.b64decode(row['data_base64'], validate=True)
                except (ValueError, binascii.Error) as exc:
                    raise EvidenceError('invalid_base64') from exc
                total += len(chunk)
                if total > 1048576:
                    raise EvidenceError('decoded_capture_limit')
                channels[row['channel']].extend(chunk)
            rows.append(row)
        except EvidenceError as exc:
            issues.append(str(exc))
            break
    observations = []
    for line in bytes(channels['stdout']).splitlines(keepends=True):
        try:
            if len(line) > 131072:
                raise EvidenceError('worker_line_limit')
            if not line.endswith(b'\n'):
                raise EvidenceError('partial_worker_line')
            value = strict_json(line)
            if type(value) is not dict:
                raise EvidenceError('worker_event_shape')
            observations.append(value)
        except EvidenceError as exc:
            issues.append(str(exc))
            break
    # stderr is never parsed as probe observations; validate text separately.
    try:
        channels['stderr'].decode('utf-8')
    except UnicodeError:
        issues.append('invalid_stderr_utf8')
    return rows, observations, sorted(set(issues)), len(channels['stderr'])


def assess_probe(directory, expectation, policy_version=1):
    if type(expectation) is not str or expectation not in EXPECTATIONS:
        raise EvidenceError('invalid_control_expectation')
    result = {'schema_version': 1, 'kind': 'probe-assessment', 'receipt_sha256': None,
              'capture_sha256': None, 'policy_sha256': POLICY_SHA256,
              'normalization_version': 1, 'program_sha256': None, 'program_identity': 'missing',
              'artifact_integrity': 'unverified', 'execution_state': 'unknown',
              'probe_assertions_status': 'unverified', 'natural_completion_status': 'unverified',
              'control_expectation': expectation, 'control_status': 'unverified',
              'benchmark_status': 'unavailable', 'model_evaluation': False,
              'assertions': [], 'reasons': [], 'run_capture_elapsed_seconds': None}
    assertions = result['assertions']
    def add(identifier, status, reason, refs=()):
        assertions.append({'id': identifier, 'status': status, 'reason': reason, 'evidence': list(refs)})
    def observed(identifier, condition, refs=()):
        add(identifier, 'pass' if condition else 'fail', 'matched' if condition else 'contradiction', refs)
    provenance_checked = False
    try:
        r, records, capture, receipt_hash = load_bundle(directory)
        result.update(receipt_sha256=receipt_hash, capture_sha256=r['capture_sha256'],
                      artifact_integrity='verified', execution_state=r.get('execution_state') if r.get('execution_state') in ('completed', 'canceled', 'timed_out', 'execution_error', 'budget_stopped') else 'unknown')
        prep, built = records['preparation.json'], records['image-build.json']
        image_input = records['image-input.json']
        initial = records['prepared.json']['container']
        stop = records[r['stop_evidence']]
        final = stop.get('container')
        binding = r['binding']
        if (prep['binding'] != binding or prep['runtime_id'] != r['runtime_id']
                or stop['runtime_id'] != r['runtime_id'] or stop['termination_confirmed'] != r['termination_confirmed']
                or built['derived_image'] != r['runtime']['derived_image']
                or initial['Image'] != built['derived_image']
                or built['base_image'] != prep['runtime']['image']
                or any(built[k] != image_input[k] for k in ('base_image', 'base_id', 'context_sha256'))):
            raise EvidenceError('provenance_mismatch')
        for container in [initial] + ([final] if final is not None else []):
            if (container['Name'] != '/' + r['runtime_id'] or container['Id'] != initial['Id']
                    or container['Image'] != built['derived_image']
                    or container['Config']['Labels'].get('ivy.attempt') != r['attempt_id']
                    or container['Config']['Labels'].get('ivy.binding') != digest(binding)):
                raise EvidenceError('ownership_or_image_mismatch')
        visible = prep.get('visible_files', {})
        if type(visible) is not dict:
            raise EvidenceError('visible_manifest_shape')
        for name, value in visible.items():
            relative_path(name)
            if type(value) is not str or not HASH.fullmatch(value):
                raise EvidenceError('visible_manifest_hash')
        program = visible.get('probe.py')
        result.update(program_sha256=program, program_identity='recognized' if program == PROGRAM_SHA256 else 'unknown' if program else 'missing')
        descriptor = r.get('program')
        if descriptor is not None and descriptor != {'id': POLICY['id'], 'sha256': program}:
            raise EvidenceError('program_descriptor_mismatch')
        if type(policy_version) is not int or policy_version != 1 or program != PROGRAM_SHA256:
            result['reasons'].append('unrecognized_program_or_policy')
            return result
        if not visible or any(not (k == 'probe.py' or k.startswith(('fixture/', 'instructions/'))) for k in visible):
            raise EvidenceError('visible_manifest_scope')
        fixtures = {k[len('fixture/'):]: v for k, v in visible.items() if k.startswith('fixture/')}
        instructions = sorted({k.split('/')[1] for k in visible if k.startswith('instructions/')})
        if not fixtures or not instructions:
            raise EvidenceError('visible_inputs_missing')
        mode = 'complete' if expectation == 'completion' else 'wait'
        for container in [initial] + ([final] if final is not None else []):
            config = container['Config']
            if (config.get('Entrypoint') != ['python3']
                    or config.get('Cmd') != ['-I', '-B', '-u', '/worker/probe.py', mode]):
                raise EvidenceError('unexpected_probe_command')
        provenance_checked = True
        rows, events, issues, stderr_count = decode_capture(capture)
        result['stderr_bytes'] = stderr_count
        result['reasons'].extend(issues)
        if rows and not issues:
            result['run_capture_elapsed_seconds'] = rows[-1]['supervisor_elapsed_seconds']
        add('capture_structure', 'unverified' if issues else 'pass', 'malformed_capture' if issues else 'parsed', ['events.jsonl'])
        expected_shapes = {'fixture_read': {'event', 'files'}, 'write_probe': {'event', 'path', 'result'},
                           'probe_ready': {'event', 'uid', 'credential_environment_present', 'visible_instruction_files'}}
        supported = all(type(e.get('event')) is str and e.get('event') in expected_shapes and set(e) == expected_shapes[e['event']] for e in events)
        add('worker_event_shapes', 'pass' if supported else 'unverified', 'supported' if supported else 'unsupported_event', ['events.jsonl'])
        def single(name, predicate=lambda e: True):
            selected = [e for e in events if e.get('event') == name and predicate(e)]
            return selected[0] if len(selected) == 1 and set(selected[0]) == expected_shapes[name] else None
        counts_ok = (sum(e.get('event') == 'fixture_read' for e in events) <= 1
                     and sum(e.get('event') == 'probe_ready' for e in events) <= 1
                     and sum(e.get('event') == 'write_probe' for e in events) <= 2)
        observed('no_duplicate_observations', counts_ok, ['events.jsonl'])
        f = single('fixture_read')
        if f is None:
            add('fixture_bytes', 'unverified', 'missing_unique_observation')
        else:
            observed('fixture_bytes', f['files'] == fixtures, ['preparation.json', 'events.jsonl'])
        ready = single('probe_ready')
        for criterion, key, expected in [('nonroot', 'uid', 65534), ('checked_credentials_absent', 'credential_environment_present', False), ('instruction_inventory', 'visible_instruction_files', instructions)]:
            if ready is None:
                add(criterion, 'unverified', 'missing_unique_readiness')
            else:
                observed(criterion, type(ready[key]) is type(expected) and ready[key] == expected, ['events.jsonl'])
        for label, path, expected in [('fixture_write', '/worker/fixture/prohibited-write', 'OSError'),
                                      ('evidence_write', '/ivy-evidence/prohibited-write', 'FileNotFoundError')]:
            event = single('write_probe', lambda e: e.get('path') == path)
            if event is None:
                add(label, 'unverified', 'missing_unique_write_observation')
            else:
                status = 'pass' if event['result'] == expected else 'fail' if event['result'] == 'write_succeeded' else 'unverified'
                add(label, status, 'write_did_not_succeed' if status == 'pass' else 'write_succeeded' if status == 'fail' else 'unsupported_exception_class', ['events.jsonl'])
        containers = [initial] + ([final] if final is not None else [])
        for i, c in enumerate(containers):
            h = c['HostConfig']
            observed('isolation_' + str(i), h.get('ReadonlyRootfs') is True and h.get('Privileged') is False
                     and h.get('NetworkMode') == 'none' and h.get('CapDrop') == ['ALL']
                     and 'no-new-privileges=true' in h.get('SecurityOpt', []) and c.get('Mounts') == []
                     and c['Config'].get('User') == '65534:65534', ['prepared.json' if i == 0 else 'stop_evidence'])
        result['probe_assertions_status'] = aggregate(a['status'] for a in assertions)
        stopped = (final is not None and stop.get('termination_confirmed') is True and r.get('termination_confirmed') is True
                   and final['State'].get('Running') is False and final['State'].get('Restarting') is False
                   and final['State'].get('Status') in ('exited', 'dead'))
        add('termination', 'pass' if stopped else 'unverified', 'confirmed_stopped' if stopped else 'shutdown_unconfirmed', ['stop_evidence'])
        starts = [x for x in rows if x['kind'] == 'start_requested']
        if not starts:
            add('start_identity', 'unverified', 'missing_start_event')
        else:
            observed('start_identity', len(starts) == 1 and rows[0]['kind'] == 'start_requested'
                     and starts[0]['runtime_id'] == r['runtime_id'], ['events.jsonl'])
        closes = [x for x in rows if x['kind'] == 'stream_closed']
        stops = [x for x in rows if x['kind'] == 'stop_requested']
        exit_code = final['State'].get('ExitCode') if final else None
        natural = aggregate(a['status'] for a in assertions)
        if not stopped:
            natural = aggregate([natural, 'unverified'])
        elif r['execution_state'] in ('canceled', 'timed_out', 'execution_error'):
            natural = 'fail'
        elif (type(exit_code) is int and exit_code != 0) or any(type(c['exit_code']) is int and c['exit_code'] != 0 for c in closes):
            natural = 'fail'
        elif r['execution_state'] != 'completed' or r.get('capture_complete') is not True or not closes or type(exit_code) is not int:
            natural = aggregate([natural, 'unverified'])
        elif (len(closes) != 1 or rows[-1]['kind'] != 'stream_closed' or stops
              or type(closes[0]['exit_code']) is not int or closes[0]['exit_code'] != 0
              or type(exit_code) is not int or exit_code != 0):
            natural = 'fail'
        result['natural_completion_status'] = natural
        if expectation == 'completion':
            add('expected_completion', natural, 'natural_completion_requirements', ['events.jsonl', 'stop_evidence'])
        else:
            if not stops:
                add('expected_stop_request', 'unverified', 'missing_stop_event')
            else:
                observed('expected_stop_request', len(stops) == 1 and stops[0]['reason'] == EXPECTATIONS[expectation]
                         and rows[-1]['kind'] == 'stop_requested' and not closes, ['events.jsonl'])
            observed('expected_terminal_state', r['execution_state'] == EXPECTATIONS[expectation] and r.get('capture_complete') is False, ['receipt.json'])
        result['control_status'] = aggregate(a['status'] for a in assertions)
        if expectation == 'completion':
            result['control_status'] = aggregate([result['control_status'], natural])
        result['coverage'] = {key: sum(a['status'] == key for a in assertions) for key in ('pass', 'fail', 'unverified')}
    except (EvidenceError, KeyError, TypeError, ValueError, AttributeError, OSError) as exc:
        code = str(exc) if isinstance(exc, EvidenceError) else 'missing_or_invalid_metadata'
        if provenance_checked:
            add('remaining_metadata', 'unverified', code)
            status = aggregate(a['status'] for a in assertions)
            result.update(control_status=status, natural_completion_status=status, probe_assertions_status=status)
            result['coverage'] = {key: sum(a['status'] == key for a in assertions) for key in ('pass', 'fail', 'unverified')}
            result['reasons'].append(code)
            return result
        # Invalid provenance is not authenticated evidence of worker failure.
        result.update(artifact_integrity='invalid' if code in ('artifact_integrity_mismatch', 'record_integrity_mismatch', 'provenance_mismatch', 'ownership_or_image_mismatch', 'capture_binding_mismatch', 'program_descriptor_mismatch') else 'unverified',
                      control_status='unverified', natural_completion_status='unverified', probe_assertions_status='unverified')
        result['assertions'] = []
        result['reasons'].append(code)
    return result


def assessment_exit(result):
    return {'pass': 0, 'fail': 1, 'unverified': 2}[result['control_status']]
