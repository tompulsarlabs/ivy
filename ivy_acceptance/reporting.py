"""Deterministic, allowlisted offline reports. Rendering never executes a workload."""
import json
from pathlib import Path
from .canonical import digest
from .evidence_io import EvidenceError, read_bytes, read_json_file, record_bytes, sha
from .probe_assessment import assess_probe, EXPECTATIONS
from .resources import aggregate_resources, empty_record, metric, validate_record
from .storage import safe_id

TITLE = 'Infrastructure proof — no model evaluation'


def report_manifest(manifest_path):
    manifest_path = Path(manifest_path)
    raw = read_bytes(manifest_path)
    from .evidence_io import strict_json
    manifest = strict_json(raw)
    if (type(manifest) is not dict or set(manifest) != {'schema_version', 'receipts', 'resources', 'expected_resource_scopes', 'sources'}
            or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1):
        raise EvidenceError('invalid_report_manifest')
    if type(manifest['receipts']) is not list or not 1 <= len(manifest['receipts']) <= 32:
        raise EvidenceError('report_receipt_limit')
    if type(manifest['resources']) is not list or len(manifest['resources']) > 256:
        raise EvidenceError('report_resource_limit')
    if type(manifest['sources']) is not dict or len(manifest['sources']) > 256:
        raise EvidenceError('report_source_limit')
    base = manifest_path.parent
    def source_path(value):
        if type(value) is not str or not value:
            raise EvidenceError('invalid_source_path')
        path = Path(value)
        return path if path.is_absolute() else base / path
    sources, source_hashes, source_data = {}, {}, {}
    for name, value in manifest['sources'].items():
        safe_id(name)
        sources[name] = source_path(value)
        source_raw = read_bytes(sources[name])
        source_hashes[name] = sha(source_raw)
        source_data[name] = strict_json(source_raw)
    selected, protected, records, ids, attempt_ids = [], [], [], set(), set()
    selected_receipts = {}
    for entry in manifest['receipts']:
        if type(entry) is not dict or set(entry) != {'id', 'directory', 'expect'} or type(entry['expect']) is not str or entry['expect'] not in EXPECTATIONS:
            raise EvidenceError('invalid_receipt_selection')
        safe_id(entry['id'])
        if entry['id'] in ids:
            raise EvidenceError('duplicate_report_receipt')
        ids.add(entry['id'])
        directory = source_path(entry['directory'])
        protected.extend([directory.resolve(), directory.resolve().parent])
        assessment = assess_probe(directory, entry['expect'])
        # Source IDs/paths never appear in public output; only user-facing safe IDs and hashes.
        receipt_hash = assessment['receipt_sha256']
        selected.append({'id': entry['id'], 'assessment': assessment})
        if receipt_hash is not None:
            source = record_bytes(read_bytes(directory / 'receipt.json'))
            attempt = source.get('attempt_id')
            safe_id(attempt)
            if attempt in attempt_ids:
                raise EvidenceError('duplicate_selected_attempt')
            attempt_ids.add(attempt)
            selected_receipts[attempt] = source
            r = empty_record(entry['id'], attempt, receipt_hash, 'receipt.json', receipt_hash)
            elapsed = assessment['run_capture_elapsed_seconds']
            if elapsed is not None:
                r['metrics']['run_capture_elapsed_seconds'] = metric(elapsed, basis='reported', reason='supervisor_start_to_last_captured_event_excludes_preparation_and_cleanup')
            records.append(r)
    # Explicit records replace the default unknown record for that scope, never add to it.
    provided, provided_scopes = [], set()
    def check_time_source(record):
        for key in ('run_capture_elapsed_seconds', 'whole_command_elapsed_seconds', 'reserved_seconds', 'engineering_elapsed_seconds'):
            m = record['metrics'][key]
            if m['basis'] != 'reported':
                continue
            matches = []
            for item in selected:
                a = item['assessment']
                if a['receipt_sha256'] == record['receipt_sha256'] and key == 'run_capture_elapsed_seconds':
                    matches.append(a['run_capture_elapsed_seconds'])
            for data in source_data.values():
                if type(data) is not dict:
                    continue
                if key == 'whole_command_elapsed_seconds':
                    for row in data.get('attempts', []) if type(data.get('attempts')) is list else []:
                        if type(row) is dict and row.get('id') == record['attempt_id'] and row.get('receipt_sha256') == record['receipt_sha256']:
                            matches.append(row.get('whole_command_observed_seconds'))
                elif key == 'reserved_seconds' and set(data) == {'record', 'sha256'}:
                    if digest(data['record']) != data['sha256']:
                        raise EvidenceError('resource_ledger_integrity_mismatch')
                    body = data['record']
                    for row in body.get('attempts', []) if type(body) is dict and type(body.get('attempts')) is list else []:
                        if type(row) is dict and row.get('id') == record['attempt_id']:
                            receipt = selected_receipts.get(record['attempt_id'], {})
                            if row.get('runtime_id') != receipt.get('runtime_id') or body.get('binding') != receipt.get('binding'):
                                raise EvidenceError('resource_ledger_attempt_mismatch')
                            matches.append(row.get('seconds'))
                elif key == 'engineering_elapsed_seconds' and record['stage'] == 'engineering':
                    if 'engineering_budget_debit_seconds' in data:
                        matches.append(data['engineering_budget_debit_seconds'])
            if not matches or any(type(v) not in (int, float) or v != m['value'] for v in matches):
                raise EvidenceError('reported_time_source_mismatch')

    selected_hashes = {r['attempt_id']: r['receipt_sha256'] for r in records}
    selected_scope_bindings = {r['scope_id']: (r['attempt_id'], r['receipt_sha256']) for r in records}
    for name in manifest['resources']:
        path = source_path(name)
        record = read_json_file(path)
        validate_record(record)
        if record['scope_id'] in provided_scopes:
            raise EvidenceError('duplicate_resource_scope')
        provided_scopes.add(record['scope_id'])
        if source_hashes.get(record['source_ref']) != record['source_sha256']:
            raise EvidenceError('resource_source_mismatch')
        if record['attempt_id'] is not None and selected_hashes.get(record['attempt_id']) != record['receipt_sha256']:
            raise EvidenceError('resource_attempt_mismatch')
        if (record['scope_id'] in selected_scope_bindings
                and (record['attempt_id'], record['receipt_sha256']) != selected_scope_bindings[record['scope_id']]):
            raise EvidenceError('resource_scope_attempt_mismatch')
        check_time_source(record)
        provided.append(record)
    records = [r for r in records if r['scope_id'] not in provided_scopes] + provided
    scopes = manifest['expected_resource_scopes']
    if scopes is None:
        scopes = [{'id': e['id'], 'stage': 'setup'} for e in selected]
    if type(scopes) is not list or not all({'id': e['id'], 'stage': 'setup'} in scopes for e in selected):
        raise EvidenceError('selected_receipt_scope_missing')
    resources = aggregate_resources(records, scopes)
    # Construct the output from an allowlist, never generic metadata/worker text.
    # reason codes and evidence references come from the policy, not arbitrary source strings.
    result = {'title': TITLE, 'schema_version': 1, 'command_status': 'rendered',
              'evidence_kind': 'recorded_infrastructure_assessment', 'model_evaluation': False,
              'benchmark_status': 'unavailable', 'source_manifest_sha256': sha(raw),
              'assessments': selected, 'resources': resources,
              'source_sha256': sorted(set(source_hashes.values())),
              'resource_record_sha256': sorted(digest(r) for r in records),
              'status_counts': {s: sum(e['assessment']['control_status'] == s for e in selected) for s in ('pass', 'fail', 'unverified')},
              'limitations': ['Trusted local supervisor; hashes are not signatures.',
                              'Fixed-probe observations are not agent quality or instruction-following evidence.',
                              'Observed capture time excludes preparation and cleanup; no hard lifecycle guarantee.',
                              'Resource totals cover declared exclusive scopes only; unavailable billing is not zero.']}
    return result, protected + [p.resolve() for p in sources.values()] + [manifest_path.resolve()]


def render_markdown(result):
    lines = [TITLE, '', 'Recorded offline assessment. No model benchmark or savings claim.', '',
             '| Evidence | Expected control | Control | Natural completion | Integrity |',
             '| --- | --- | --- | --- | --- |']
    for item in result['assessments']:
        a = item['assessment']
        lines.append(f"| {item['id']} | {a['control_expectation']} | {a['control_status']} | {a['natural_completion_status']} | {a['artifact_integrity']} |")
    for item in result['assessments']:
        a = item['assessment']
        lines += ['', f"**{item['id']}**", '', f"Receipt: `{a['receipt_sha256'] or 'unavailable'}`", '',
                  '| Check | Status | Reason |', '| --- | --- | --- |']
        lines += [f"| {c['id']} | {c['status']} | {c['reason']} |" for c in a['assertions']]
        if a['reasons']:
            lines += ['', 'Evidence gaps: ' + ', '.join(a['reasons'])]
    lines += ['', '**Resource visibility**', '', '| Group / metric | Reported subtotal | Estimated subtotal | Unknown scopes | Complete reported total |',
              '| --- | ---: | ---: | ---: | ---: |']
    def number(value):
        return 'Unavailable' if value is None else str(value) if type(value) is int else format(value, '.9g')
    for group, values in result['resources']['groups'].items():
        for key, v in values['metrics'].items():
            if values['expected_scope_ids']:
                lines.append(f"| {group} / {key} ({v['unit'] or 'currency unknown'}) | {number(v['reported_subtotal'])} | {number(v['estimated_subtotal'])} | {v['unknown_scope_count']} | {number(v['complete_reported_total'])} |")
    lines += ['', 'Cost per accepted primary task: **Unavailable — no model primary assessments.**', '', '**Limits of this evidence**', '']
    lines += ['- ' + s for s in result['limitations']]
    return '\n'.join(lines) + '\n'


def write_report(manifest_path, output_directory):
    result, protected = report_manifest(manifest_path)
    output = Path(output_directory)
    resolved = output.resolve()
    if any(resolved == path or path in resolved.parents or resolved in path.parents for path in protected):
        raise EvidenceError('report_output_overlaps_sources')
    if output.exists() or output.is_symlink():
        raise EvidenceError('report_output_exists')
    output.mkdir(parents=True, mode=0o700)
    # Directory exclusively created; no existing report or evidence can be overwritten.
    (output / 'report.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    (output / 'report.sha256').write_text(digest(result) + '\n')
    (output / 'report.md').write_text(render_markdown(result))
    return {'command_status': 'rendered', 'report_sha256': digest(result),
            'status_counts': result['status_counts'], 'model_evaluation': False, 'benchmark_status': 'unavailable'}
