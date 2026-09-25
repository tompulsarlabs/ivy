"""Exclusive, source-bound observations; no price estimator or accepted-task claims."""
import re
from decimal import Decimal
from .evidence_io import EvidenceError, finite_number
from .storage import safe_id

METRICS = {'request_count': 'count', 'input_tokens': 'tokens', 'output_tokens': 'tokens',
           'cached_input_tokens': 'tokens', 'billed_amount': 'currency',
           'run_capture_elapsed_seconds': 'seconds', 'whole_command_elapsed_seconds': 'seconds',
           'reserved_seconds': 'seconds', 'engineering_elapsed_seconds': 'seconds'}
STAGES = {'setup', 'coordinator', 'worker', 'grader', 'engineering'}
HASH = re.compile(r'[0-9a-f]{64}')


def metric(value=None, unit='seconds', basis='unknown', reason='not_observed'):
    return {'value': value, 'unit': unit, 'basis': basis, 'reason': reason}


def validate_record(record):
    keys = {'schema_version', 'id', 'scope_id', 'parent_scope_id', 'stage', 'accounting',
            'source_ref', 'source_sha256', 'attempt_id', 'receipt_sha256', 'metrics'}
    if (type(record) is not dict or set(record) != keys or type(record['schema_version']) is not int
            or record['schema_version'] != 1 or record['accounting'] != 'exclusive'
            or type(record['stage']) is not str or record['stage'] not in STAGES):
        raise EvidenceError('invalid_resource_record')
    for key in ('id', 'scope_id', 'source_ref'):
        safe_id(record[key])
    if record['parent_scope_id'] is not None:
        safe_id(record['parent_scope_id'])
        if record['parent_scope_id'] == record['scope_id']:
            raise EvidenceError('resource_parent_cycle')
    if type(record['source_sha256']) is not str or not HASH.fullmatch(record['source_sha256']):
        raise EvidenceError('missing_resource_source_binding')
    if (record['attempt_id'] is None) != (record['receipt_sha256'] is None):
        raise EvidenceError('incomplete_resource_attempt_binding')
    if record['attempt_id'] is not None:
        safe_id(record['attempt_id'])
        if type(record['receipt_sha256']) is not str or not HASH.fullmatch(record['receipt_sha256']):
            raise EvidenceError('invalid_resource_receipt_binding')
    metrics = record['metrics']
    if type(metrics) is not dict or set(metrics) != set(METRICS):
        raise EvidenceError('resource_metrics_must_be_explicit')
    for key, m in metrics.items():
        if type(m) is not dict or set(m) != {'value', 'unit', 'basis', 'reason'}:
            raise EvidenceError('invalid_metric_shape')
        if m['basis'] not in ('reported', 'estimated', 'unknown') or type(m['reason']) is not str or not m['reason'].strip() or len(m['reason']) > 500:
            raise EvidenceError('invalid_metric_origin')
        if key == 'billed_amount':
            if m['unit'] is not None and (type(m['unit']) is not str or not re.fullmatch('[A-Z]{3}', m['unit'])):
                raise EvidenceError('invalid_currency')
        elif m['unit'] != METRICS[key]:
            raise EvidenceError('invalid_metric_unit')
        if m['basis'] == 'unknown':
            if m['value'] is not None:
                raise EvidenceError('unknown_metric_requires_null')
        elif (not finite_number(m['value']) or m['unit'] is None
              or (key in ('request_count', 'input_tokens', 'output_tokens', 'cached_input_tokens') and type(m['value']) is not int)):
            raise EvidenceError('invalid_metric_number')
    a, b = metrics['cached_input_tokens'], metrics['input_tokens']
    if a['basis'] == b['basis'] != 'unknown' and a['value'] > b['value']:
        raise EvidenceError('cached_input_exceeds_input')
    return record


def empty_record(scope_id, attempt_id, receipt_hash, source_ref, source_hash, *, stage='setup'):
    return {'schema_version': 1, 'id': scope_id, 'scope_id': scope_id, 'parent_scope_id': None,
            'stage': stage, 'accounting': 'exclusive', 'source_ref': source_ref, 'source_sha256': source_hash,
            'attempt_id': attempt_id, 'receipt_sha256': receipt_hash,
            'metrics': {k: metric(unit=None if u == 'currency' else u) for k, u in METRICS.items()}}


def aggregate_resources(records, expected_scopes):
    if type(expected_scopes) is not list or not expected_scopes or len(expected_scopes) > 256:
        raise EvidenceError('invalid_expected_resource_scopes')
    expected = {}
    for scope in expected_scopes:
        if type(scope) is not dict or set(scope) != {'id', 'stage'} or type(scope['stage']) is not str or scope['stage'] not in STAGES:
            raise EvidenceError('invalid_resource_scope')
        safe_id(scope['id'])
        if scope['id'] in expected:
            raise EvidenceError('duplicate_expected_scope')
        expected[scope['id']] = scope['stage']
    if type(records) is not list or len(records) > 256:
        raise EvidenceError('resource_record_limit')
    found, ids = {}, set()
    for r in records:
        validate_record(r)
        if r['id'] in ids or r['scope_id'] in found:
            raise EvidenceError('duplicate_resource_scope_or_id')
        if expected.get(r['scope_id']) != r['stage']:
            raise EvidenceError('undeclared_resource_scope')
        found[r['scope_id']] = r
        ids.add(r['id'])
    for key, r in found.items():
        seen, parent = {key}, r['parent_scope_id']
        while parent is not None:
            if parent in seen or parent not in expected:
                raise EvidenceError('invalid_resource_parent_graph')
            seen.add(parent)
            parent = found[parent]['parent_scope_id'] if parent in found else None
    def total(values):
        if not values:
            return None
        value = sum(values) if all(type(v) is int for v in values) else float(sum(Decimal(str(v)) for v in values))
        if not finite_number(value):
            raise EvidenceError('resource_total_overflow')
        return value
    groups = {}
    for group in ('execution', 'engineering'):
        scopes = sorted(k for k, stage in expected.items() if (stage == 'engineering') == (group == 'engineering'))
        totals = {}
        for name, default_unit in METRICS.items():
            values = [found[k]['metrics'][name] for k in scopes if k in found]
            units = {v['unit'] for v in values if v['unit'] is not None}
            if len(units) > 1:
                raise EvidenceError('mixed_metric_currencies_or_units')
            reported = [v['value'] for v in values if v['basis'] == 'reported']
            estimated = [v['value'] for v in values if v['basis'] == 'estimated']
            unknown = len(scopes) - len(reported) - len(estimated)
            totals[name] = {'unit': next(iter(units), None if default_unit == 'currency' else default_unit),
                            'reported_subtotal': total(reported),
                            'estimated_subtotal': total(estimated),
                            'reported_scope_count': len(reported), 'estimated_scope_count': len(estimated),
                            'unknown_scope_count': unknown,
                            'complete_reported_total': total(reported) if scopes and len(reported) == len(scopes) else None}
        groups[group] = {'expected_scope_ids': scopes, 'missing_scope_ids': [k for k in scopes if k not in found], 'metrics': totals}
    return {'schema_version': 1, 'scope': 'declared_exclusive_components_only', 'groups': groups,
            'cost_per_accepted_primary_task': {'value': None, 'reason': 'no_model_primary_assessments'}}
