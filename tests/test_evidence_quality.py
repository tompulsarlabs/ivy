"""EQ01–EQ12: independent software controls, never counted as model evaluations."""
import base64
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ivy_acceptance.canonical import canonical_bytes, digest
from ivy_acceptance.docker_probe import PROBE
from ivy_acceptance.evidence_io import EvidenceError, MAX_FILE, sha
from ivy_acceptance.probe_assessment import PROGRAM_SHA256, assess_probe, assessment_exit, decode_capture
from ivy_acceptance.probe_cli import command_exit, declared_expectation, verify_probe
from ivy_acceptance.resources import aggregate_resources, empty_record, metric, validate_record
from ivy_acceptance.reporting import report_manifest, write_report, render_markdown
from ivy_acceptance.storage import write_record, read_record, file_sha256

ROOT = Path(__file__).resolve().parents[1]


class Bundle:
    """Independently specified synthetic record set, not copied from a real receipt."""
    def __init__(self, path, expectation='completion'):
        self.path = path
        path.mkdir()
        self.binding = {'purpose': 'synthetic_software_control'}
        self.image = 'sha256:' + 'd' * 64
        self.fixture = {'task.md': sha(b'Neutral task\n'), 'head/a.py': sha(b'return 1\n')}
        self.worker = [
            {'event': 'fixture_read', 'files': self.fixture},
            {'event': 'write_probe', 'path': '/worker/fixture/prohibited-write', 'result': 'OSError'},
            {'event': 'write_probe', 'path': '/ivy-evidence/prohibited-write', 'result': 'FileNotFoundError'},
            {'event': 'probe_ready', 'uid': 65534, 'credential_environment_present': False, 'visible_instruction_files': ['AGENTS.md']},
        ]
        mode = 'complete' if expectation == 'completion' else 'wait'
        initial = {'Id': 'synthetic-container-id', 'Name': '/synthetic-container', 'Image': self.image,
                   'Config': {'Labels': {'ivy.attempt': 'synthetic-attempt', 'ivy.binding': digest(self.binding)},
                              'Entrypoint': ['python3'], 'Cmd': ['-I', '-B', '-u', '/worker/probe.py', mode], 'User': '65534:65534'},
                   'HostConfig': {'ReadonlyRootfs': True, 'Privileged': False, 'NetworkMode': 'none', 'CapDrop': ['ALL'], 'SecurityOpt': ['no-new-privileges=true']},
                   'Mounts': [], 'State': {'Status': 'created', 'Running': False, 'Restarting': False, 'ExitCode': 0}}
        final = copy.deepcopy(initial)
        final['State']['Status'] = 'exited'
        if expectation != 'completion':
            final['State']['ExitCode'] = 137
        visible = {'fixture/' + k: v for k, v in self.fixture.items()}
        visible.update({'instructions/AGENTS.md': sha(b'Instructions'), 'probe.py': PROGRAM_SHA256})
        image_input = {'base_image': 'python@sha256:' + 'a' * 64, 'base_id': 'sha256:' + 'a' * 64, 'context_sha256': 'c' * 64}
        self.records = {'preparation.json': {'runtime_id': 'synthetic-container', 'binding': self.binding,
                          'runtime': {'image': image_input['base_image']}, 'visible_files': visible},
                        'prepared.json': {'container': initial},
                        'image-input.json': image_input,
                        'image-build.json': {**image_input, 'derived_image': self.image},
                        'stop-synthetic.json': {'runtime_id': 'synthetic-container', 'termination_confirmed': True, 'container': final}}
        self.receipt = {'schema_version': 1, 'evidence_kind': 'infrastructure_probe_not_model_evaluation',
                        'attempt_id': 'synthetic-attempt', 'runtime_id': 'synthetic-container', 'binding': self.binding,
                        'runtime': {'derived_image': self.image}, 'stop_evidence': 'stop-synthetic.json',
                        'execution_state': {'completion': 'completed', 'cancellation': 'canceled', 'deadline': 'timed_out'}[expectation],
                        'capture_complete': expectation == 'completion', 'termination_confirmed': True}
        self.expectation = expectation
        self.rows = []
        self.set_worker(self.worker)

    def set_worker(self, worker, chunks=None):
        encoded = b''.join(canonical_bytes(e) + b'\n' for e in worker)
        chunks = chunks if chunks is not None else [encoded]
        self.rows = [{'kind': 'start_requested', 'runtime_id': 'synthetic-container'}]
        self.rows += [{'kind': 'worker_stream', 'channel': 'stdout', 'data_base64': base64.b64encode(chunk).decode()} for chunk in chunks]
        self.rows += [{'kind': 'stream_closed', 'exit_code': 0}] if self.expectation == 'completion' else [{'kind': 'stop_requested', 'reason': self.receipt['execution_state']}]
        for index, row in enumerate(self.rows, 1):
            row.update(sequence=index, supervisor_elapsed_seconds=index / 10)
        self.save()

    def save(self, raw=None):
        for name, body in self.records.items():
            write_record(self.path / name, body)
        (self.path / 'events.jsonl').write_bytes(raw if raw is not None else b''.join(canonical_bytes(r) + b'\n' for r in self.rows))
        self.receipt['artifact_sha256'] = {name: file_sha256(self.path / name) for name in [*self.records, 'events.jsonl']}
        self.receipt['capture_sha256'] = self.receipt['artifact_sha256']['events.jsonl']
        write_record(self.path / 'receipt.json', self.receipt)


class EvidenceQualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'store').mkdir()
        self.bundle = Bundle(self.root / 'store' / 'attempt')

    def assess(self, expectation='completion'):
        return assess_probe(self.bundle.path, expectation)

    def test_eq01_complete_known_probe(self):
        self.assertEqual(hashlib.sha256(PROBE).hexdigest(), PROGRAM_SHA256)
        a = self.assess()
        self.assertEqual(a['control_status'], 'pass')
        self.assertEqual(a['natural_completion_status'], 'pass')
        self.assertFalse(a['model_evaluation'])
        self.assertEqual(a['benchmark_status'], 'unavailable')

    def test_eq02_interruption_controls_do_not_complete(self):
        for expectation in ('cancellation', 'deadline'):
            b = Bundle(self.root / expectation, expectation)
            a = assess_probe(b.path, expectation)
            self.assertEqual(a['control_status'], 'pass')
            self.assertEqual(a['natural_completion_status'], 'fail')
            self.assertFalse(b.receipt['capture_complete'])

    def test_eq03_empty_irrelevant_missing(self):
        for observations in ([], [{'event': 'irrelevant'}], self.bundle.worker[:-1]):
            self.bundle.set_worker(observations)
            self.assertEqual(self.assess()['control_status'], 'unverified')
        self.bundle.save(raw=b'')
        self.assertEqual(self.assess()['control_status'], 'unverified')

    def test_eq04_known_failure_outweighs_missing(self):
        worker = copy.deepcopy(self.bundle.worker[:-1])
        worker[1]['result'] = 'write_succeeded'
        self.bundle.set_worker(worker)
        a = self.assess()
        self.assertEqual(a['control_status'], 'fail')
        self.assertTrue(any(c['status'] == 'unverified' for c in a['assertions']))

    def test_eq04_missing_later_metadata_preserves_failure(self):
        self.bundle.worker[1]['result'] = 'write_succeeded'
        self.bundle.set_worker(self.bundle.worker)
        del self.bundle.records['stop-synthetic.json']['container']['HostConfig']
        self.bundle.save()
        result = self.assess()
        self.assertEqual(result['control_status'], 'fail')
        self.assertEqual(result['artifact_integrity'], 'verified')
        self.assertTrue(any(a['status'] == 'unverified' for a in result['assertions']))

    def test_eq08_invalid_nested_metadata_is_unverified(self):
        original = copy.deepcopy(self.bundle.records)
        for filename, field in [('prepared.json', 'Config'), ('prepared.json', 'HostConfig'), ('stop-synthetic.json', 'State')]:
            self.bundle.records = copy.deepcopy(original)
            self.bundle.records[filename]['container'][field] = []
            self.bundle.save()
            self.assertEqual(self.assess()['control_status'], 'unverified')

    def test_eq08_unhashable_event_fields_are_unverified(self):
        for field in ('kind', 'channel'):
            self.bundle.set_worker(self.bundle.worker)
            self.bundle.rows[1][field] = []
            self.bundle.save()
            self.assertEqual(self.assess()['control_status'], 'unverified')
        self.bundle.worker.append({'event': []})
        self.bundle.set_worker(self.bundle.worker)
        self.assertEqual(self.assess()['control_status'], 'unverified')

    def test_eq05_tampering_and_wrong_owner(self):
        original = (self.bundle.path / 'events.jsonl').read_bytes()
        (self.bundle.path / 'events.jsonl').write_bytes(original + b'changed')
        self.assertEqual(self.assess()['artifact_integrity'], 'invalid')
        self.bundle.save()
        self.bundle.records['stop-synthetic.json']['container']['Config']['Labels']['ivy.attempt'] = 'different-owner'
        self.bundle.save()
        self.assertEqual(self.assess()['artifact_integrity'], 'invalid')

    def test_eq06_legacy_unknown_and_descriptor(self):
        visible = self.bundle.records['preparation.json']['visible_files']
        for value in (None, 'e' * 64):
            if value is None:
                visible.pop('probe.py', None)
            else:
                visible['probe.py'] = value
            self.bundle.save()
            self.assertEqual(self.assess()['control_status'], 'unverified')
        visible['probe.py'] = PROGRAM_SHA256
        self.bundle.save()
        self.assertEqual(assess_probe(self.bundle.path, 'completion', 2)['control_status'], 'unverified')
        self.bundle.receipt['program'] = {'id': 'another', 'sha256': PROGRAM_SHA256}
        self.bundle.save()
        self.assertEqual(self.assess()['control_status'], 'unverified')

    def test_eq07_split_json_unicode_and_stderr(self):
        self.bundle.fixture['head/caf\u00e9.py'] = 'e' * 64
        self.bundle.records['preparation.json']['visible_files']['fixture/head/caf\u00e9.py'] = 'e' * 64
        data = b''.join(canonical_bytes(e) + b'\n' for e in self.bundle.worker)
        self.bundle.set_worker(self.bundle.worker, [data[i:i+1] for i in range(len(data))])
        baseline = self.assess()
        self.assertEqual(baseline['control_status'], 'pass')
        self.bundle.rows.insert(2, {'kind': 'worker_stream', 'channel': 'stderr', 'data_base64': base64.b64encode(b'{"event":"probe_ready"}\n').decode()})
        for i, r in enumerate(self.bundle.rows, 1):
            r.update(sequence=i, supervisor_elapsed_seconds=i / 1000)
        self.bundle.save()
        self.assertEqual(self.assess()['control_status'], 'pass')

    def test_eq08_malformed_stream_limits_and_duplicates(self):
        original = copy.deepcopy(self.bundle.rows)
        for mutation in ('base64', 'sequence', 'time', 'shape', 'partial', 'duplicate-key', 'oversize'):
            self.bundle.rows = copy.deepcopy(original)
            raw = None
            if mutation == 'base64': self.bundle.rows[1]['data_base64'] = '!'
            if mutation == 'sequence': self.bundle.rows[1]['sequence'] = 99
            if mutation == 'time': self.bundle.rows[1]['supervisor_elapsed_seconds'] = -1
            if mutation == 'shape': self.bundle.rows[1]['extra'] = True
            if mutation == 'partial': raw = b'{'
            if mutation == 'duplicate-key': raw = b'{"kind":"x","kind":"y"}\n'
            if mutation == 'oversize': raw = b' ' * (MAX_FILE + 1)
            self.bundle.save(raw)
            self.assertNotEqual(self.assess()['control_status'], 'pass', mutation)
        self.bundle.set_worker(self.bundle.worker + [self.bundle.worker[0]])
        self.assertNotEqual(self.assess()['control_status'], 'pass')
        self.bundle.set_worker(self.bundle.worker, [b'{"event":'])
        self.assertNotEqual(self.assess()['control_status'], 'pass')

    def test_eq09_exit_stop_reason_and_exception(self):
        self.bundle.records['stop-synthetic.json']['container']['State']['ExitCode'] = 7
        self.bundle.receipt['capture_complete'] = False
        self.bundle.save()
        self.assertEqual(self.assess()['control_status'], 'fail')
        self.bundle.records['stop-synthetic.json']['container']['State']['ExitCode'] = 0
        self.bundle.receipt['capture_complete'] = True
        self.bundle.records['stop-synthetic.json']['termination_confirmed'] = False
        self.bundle.receipt['termination_confirmed'] = False
        self.bundle.save()
        self.assertEqual(self.assess()['control_status'], 'unverified')
        b = Bundle(self.root / 'cancel', 'cancellation')
        b.rows[-1]['reason'] = 'timed_out'
        b.save()
        self.assertEqual(assess_probe(b.path, 'cancellation')['control_status'], 'fail')
        b.worker[1]['result'] = 'PermissionError'
        b.set_worker(b.worker)
        self.assertEqual(assess_probe(b.path, 'cancellation')['control_status'], 'unverified')

    def test_eq11_cli_exits_and_no_runtime_on_invalid_options(self):
        self.assertEqual(command_exit(self.assess()), 0)
        self.bundle.set_worker([])
        self.assertEqual(command_exit(self.assess()), 2)
        proc = subprocess.run([sys.executable, '-B', '-m', 'ivy_acceptance', 'assess-probe', str(self.bundle.path), '--expect', 'completion'], cwd=ROOT, capture_output=True)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)['control_status'], 'unverified')
        from types import SimpleNamespace
        with self.assertRaises(EvidenceError):
            declared_expectation(SimpleNamespace(deadline=10, wait=False, cancel_after=2))
        b = Bundle(self.root / 'partial', 'cancellation')
        self.assertEqual(verify_probe(b.path)['verification_scope'], 'artifact_integrity_only')
        self.assertEqual(command_exit(verify_probe(b.path)), 0)


class ResourceQualityTests(unittest.TestCase):
    def record(self, scope='one'):
        return empty_record(scope, 'attempt', 'a'*64, 'source.json', 'b'*64)

    def scopes(self, *ids):
        return [{'id': i, 'stage': 'setup'} for i in ids]

    def test_eq10_unknown_zero_estimates_and_missing_scope(self):
        r = self.record()
        r['metrics']['billed_amount'] = metric(0, 'USD', 'reported', 'source_records_zero')
        summary = aggregate_resources([r], self.scopes('one', 'two'))
        money = summary['groups']['execution']['metrics']['billed_amount']
        self.assertEqual(money['reported_subtotal'], 0)
        self.assertIsNone(money['complete_reported_total'])
        self.assertEqual(money['unknown_scope_count'], 1)
        other = self.record('two')
        other['metrics']['billed_amount'] = metric(2, 'USD', 'estimated', 'operator_estimate')
        money = aggregate_resources([r, other], self.scopes('one', 'two'))['groups']['execution']['metrics']['billed_amount']
        self.assertEqual(money['estimated_subtotal'], 2)
        self.assertIsNone(money['complete_reported_total'])
        self.assertIsNone(summary['cost_per_accepted_primary_task']['value'])

    def test_eq10_unhashable_stage_rejected(self):
        r = self.record()
        r['stage'] = []
        with self.assertRaises(EvidenceError):
            validate_record(r)
        with self.assertRaises(EvidenceError):
            aggregate_resources([], [{'id': 'one', 'stage': []}])

    def test_eq10_invalid_numbers_units_currency_duplicates(self):
        for value in (True, -1, float('nan'), float('inf')):
            r = self.record();r['metrics']['request_count'] = metric(value, 'count', 'reported', 'source')
            with self.assertRaises(EvidenceError): validate_record(r)
        r = self.record();r['accounting'] = 'inclusive'
        with self.assertRaises(EvidenceError): validate_record(r)
        r = self.record();r['metrics']['reserved_seconds']['unit'] = 'tokens'
        with self.assertRaises(EvidenceError): validate_record(r)
        r = self.record()
        with self.assertRaises(EvidenceError): aggregate_resources([r, r], self.scopes('one'))
        r['metrics']['billed_amount'] = metric(1, 'USD', 'reported', 'source')
        other = self.record('two');other['metrics']['billed_amount'] = metric(1, 'EUR', 'reported', 'source')
        with self.assertRaises(EvidenceError): aggregate_resources([r, other], self.scopes('one', 'two'))


class ReportQualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'store').mkdir()
        self.bundle = Bundle(self.root / 'store' / 'attempt')
        self.manifest = {'schema_version': 1, 'receipts': [{'id': 'completion', 'directory': 'store/attempt', 'expect': 'completion'}],
                         'resources': [], 'sources': {}, 'expected_resource_scopes': None}
        self.path = self.root / 'manifest.json'
        self.save()

    def save(self):
        self.path.write_bytes(canonical_bytes(self.manifest))

    def test_eq11_report_renders_same_result_and_refuses_overwrite_overlap(self):
        result, _ = report_manifest(self.path)
        receipt_before = (self.bundle.path / 'receipt.json').read_bytes()
        a = write_report(self.path, self.root / 'output')
        b = write_report(self.path, self.root / 'second')
        self.assertEqual(a['report_sha256'], b['report_sha256'])
        self.assertEqual(a['status_counts'], {'pass': 1, 'fail': 0, 'unverified': 0})
        rendered = json.loads((self.root / 'output/report.json').read_text())
        self.assertEqual(rendered, result)
        self.assertEqual((self.root / 'output/report.md').read_text(), render_markdown(result))
        self.assertEqual(receipt_before, (self.bundle.path / 'receipt.json').read_bytes())
        for path in (self.root / 'output', self.bundle.path / 'report', self.root / 'store/report'):
            with self.assertRaises(EvidenceError): write_report(self.path, path)
        self.bundle.set_worker([])
        failed = write_report(self.path, self.root / 'incomplete')
        self.assertEqual(failed['command_status'], 'rendered')
        self.assertEqual(failed['status_counts']['unverified'], 1)

    def test_eq10_report_validates_duration_source_not_just_claim(self):
        receipt_hash = file_sha256(self.bundle.path / 'receipt.json')
        source = {'attempts': [{'id': 'synthetic-attempt', 'receipt_sha256': receipt_hash, 'whole_command_observed_seconds': 2.5}]}
        sp = self.root / 'measurement.json';sp.write_bytes(canonical_bytes(source))
        record = empty_record('completion', 'synthetic-attempt', receipt_hash, 'measurement', file_sha256(sp))
        record['metrics']['whole_command_elapsed_seconds'] = metric(2.5, basis='reported', reason='command_measurement')
        rp = self.root / 'resource.json';rp.write_bytes(canonical_bytes(record))
        self.manifest.update(sources={'measurement': 'measurement.json'}, resources=['resource.json'])
        self.save()
        result, _ = report_manifest(self.path)
        self.assertEqual(result['resources']['groups']['execution']['metrics']['whole_command_elapsed_seconds']['complete_reported_total'], 2.5)
        record['metrics']['whole_command_elapsed_seconds']['value'] = 9
        rp.write_bytes(canonical_bytes(record))
        with self.assertRaises(EvidenceError): report_manifest(self.path)
        record['metrics']['whole_command_elapsed_seconds'] = metric()
        record['attempt_id'] = record['receipt_sha256'] = None
        rp.write_bytes(canonical_bytes(record))
        with self.assertRaisesRegex(EvidenceError, 'resource_scope_attempt_mismatch'):
            report_manifest(self.path)

    def test_eq05_symlink_metadata_rejected(self):
        path = self.bundle.path / 'prepared.json'
        data = path.read_bytes();other = self.root / 'copied.json';other.write_bytes(data)
        path.unlink();path.symlink_to(other)
        self.assertNotEqual(assess_probe(self.bundle.path, 'completion')['control_status'], 'pass')

    def test_eq08_nested_json_and_oversize_manifest(self):
        from ivy_acceptance.evidence_io import strict_json
        with self.assertRaises(EvidenceError): strict_json(b'[' * 17 + b'0' + b']' * 17)
        self.manifest['receipts'] *= 33
        self.save()
        with self.assertRaises(EvidenceError): report_manifest(self.path)

    def test_eq12_replay_is_reproducible_with_no_external_effects(self):
        # Portable synthetic controls for CI. Actual private-receipt replay is recorded separately.
        for name, expectation in [('cancel', 'cancellation'), ('timeout', 'deadline')]:
            b = Bundle(self.root / 'store' / name, expectation)
            b.receipt['attempt_id'] = name
            for key in ('prepared.json', 'stop-synthetic.json'):
                b.records[key]['container']['Config']['Labels']['ivy.attempt'] = name
            b.save()
            self.manifest['receipts'].append({'id': name, 'directory': 'store/' + name, 'expect': expectation})
        self.save()
        before = {str(p): p.read_bytes() for p in (self.root / 'store').rglob('*') if p.is_file()}
        with patch('subprocess.run', side_effect=AssertionError('no processes in offline report')):
            a = write_report(self.path, self.root / 'replay')
        self.assertEqual(a['status_counts']['pass'], 3)
        self.assertEqual(before, {str(p): p.read_bytes() for p in (self.root / 'store').rglob('*') if p.is_file()})


class ProbeCommandWiringTests(unittest.TestCase):
    def test_probe_cli_failure_returns_one_from_assessment(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from ivy_acceptance.__main__ import main
        from ivy_acceptance.ports import ExecutionState
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            store = Path(temp) / 'store';store.mkdir()
            b = Bundle(store / 'attempt')
            b.receipt['execution_state'] = 'execution_error';b.save()
            argv = ['probe', str(ROOT / 'examples/acceptance/preview.json'), '--root', str(ROOT),
                    '--store', str(store), '--attempt', 'attempt', '--image', 'unused-by-mocked-adapter', '--context', 'unused']
            with patch('ivy_acceptance.probe_cli.DockerProbeAdapter') as adapter:
                adapter.return_value.run.return_value = SimpleNamespace(execution_state=ExecutionState.EXECUTION_ERROR)
                with redirect_stdout(StringIO()) as output:
                    code = main(argv)
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.getvalue())['assessment']['control_status'], 'fail')

    def test_bad_options_fail_before_store_or_adapter(self):
        from types import SimpleNamespace
        from ivy_acceptance.probe_cli import run_command
        with patch('ivy_acceptance.probe_cli.AttemptStore', side_effect=AssertionError('must not reserve')):
            with self.assertRaises(EvidenceError):
                run_command(SimpleNamespace(command='probe', deadline=10, wait=False, cancel_after=1))
