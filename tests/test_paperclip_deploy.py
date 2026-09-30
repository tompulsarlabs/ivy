"""Deployment gates, independent of Docker, Paperclip and provider credentials."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "paperclip_preflight", Path(__file__).parents[1] / "deploy/paperclip/preflight.py")
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def valid():
    return {
        "PAPERCLIP_DEPLOYMENT_MODE": "authenticated",
        "PAPERCLIP_DEPLOYMENT_EXPOSURE": "public",
        "PAPERCLIP_HOME": "/paperclip",
        "HEARTBEAT_SCHEDULER_ENABLED": "false",
        "PAPERCLIP_AUTH_PUBLIC_BASE_URL": "https://ivy.example.com",
        "PAPERCLIP_ALLOWED_HOSTNAMES": "ivy.example.com,healthcheck.railway.app",
        "BETTER_AUTH_SECRET": "only-a-test-secret-never-used-in-a-deployment-12345",
        "PAPERCLIP_SECRETS_MASTER_KEY": base64.b64encode(bytes(range(32))).decode(),
        "DATABASE_URL": "postgresql://user:test-password@database.internal:5432/paperclip",
    }


class PaperclipDeployTests(unittest.TestCase):
    def test_valid_board_environment(self):
        self.assertEqual(preflight.validate_environment(valid()), [])

    def test_public_trusted_or_active_scheduler_refused(self):
        for name, value in [("PAPERCLIP_DEPLOYMENT_MODE", "local_trusted"),
                            ("PAPERCLIP_DEPLOYMENT_EXPOSURE", "private"),
                            ("HEARTBEAT_SCHEDULER_ENABLED", "true"),
                            ("PAPERCLIP_HOME", "/tmp/transient")]:
            with self.subTest(name=name):
                self.assertTrue(preflight.validate_environment({**valid(), name: value}))

    def test_unsafe_and_conflicting_origins_refused(self):
        for origin in ["http://ivy.example.com", "https://secret@ivy.example.com",
                       "https://ivy.example.com/x", "https://ivy.example.com?secret=yes",
                       "https://ivy.example.com:bad", "https://ivy.example.com:444", "https://["]:
            with self.subTest(origin=origin):
                self.assertIn("invalid_https_origin", preflight.validate_environment(
                    {**valid(), "PAPERCLIP_AUTH_PUBLIC_BASE_URL": origin}))
        self.assertIn("conflicting_auth_origin", preflight.validate_environment(
            {**valid(), "PAPERCLIP_PUBLIC_URL": "https://different.example.com"}))

    def test_wildcard_missing_and_unrelated_hosts_refused(self):
        for hosts in ["*", "", "other.example.com", "ivy.example.com,evil.example.com"]:
            self.assertIn("invalid_allowed_hostnames", preflight.validate_environment(
                {**valid(), "PAPERCLIP_ALLOWED_HOSTNAMES": hosts}))

    def test_missing_placeholder_or_invalid_secrets_refused_without_disclosure(self):
        for name, values in {
            "BETTER_AUTH_SECRET": ["", "change-me", "a" * 64],
            "PAPERCLIP_SECRETS_MASTER_KEY": ["", "not-base64", base64.b64encode(b"x" * 32).decode()],
            "DATABASE_URL": ["", "postgresql://user@db/paperclip", "postgres://user:SECRET@db:bad/db"],
        }.items():
            for value in values:
                with self.subTest(name=name):
                    errors = preflight.validate_environment({**valid(), name: value})
                    self.assertTrue(errors)
                    self.assertNotIn("SECRET", str(errors))

    def test_model_credentials_not_accepted_by_board_release(self):
        self.assertEqual(preflight.validate_environment({**valid(), "OPENAI_API_KEY": "never-print-this"}),
                         ["model_credentials_not_allowed_in_board_release"])

    def test_plain_ephemeral_directory_is_not_a_volume(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(preflight.check_storage(Path(directory)), ["persistent_app_volume_missing"])

    def test_unwritable_volume_refused(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(preflight.os.path, "ismount", return_value=True), \
                patch.object(preflight.tempfile, "TemporaryFile", side_effect=PermissionError):
            self.assertEqual(preflight.check_storage(Path(directory)), ["persistent_app_volume_not_writable"])

    def test_writable_volume_probe_leaves_no_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(preflight.os.path, "ismount", return_value=True):
            self.assertEqual(preflight.check_storage(Path(directory)), [])
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_cli_config_is_private_and_restart_does_not_overwrite_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(preflight.ensure_config(valid(), root), [])
            path = root / "instances/default/config.json"
            original = path.read_bytes()
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(original)["server"]["deploymentMode"], "authenticated")
            self.assertEqual(preflight.ensure_config(valid(), root), [])
            self.assertEqual(path.read_bytes(), original)
            changed = {**valid(), "DATABASE_URL": "postgres://user:password@other/db"}
            self.assertEqual(preflight.ensure_config(changed, root), ["persisted_database_config_differs_from_environment"])
            self.assertEqual(path.read_bytes(), original)

    def test_malformed_existing_config_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "instances/default/config.json"
            path.parent.mkdir(parents=True)
            path.write_text("broken")
            self.assertEqual(preflight.ensure_config(valid(), root), ["persistent_config_unavailable"])
            self.assertEqual(path.read_text(), "broken")

    def test_runtime_sets_the_same_public_origin_for_csrf_and_login(self):
        with patch.dict(os.environ, valid(), clear=True), \
                patch.object(preflight, "check_storage", return_value=[]), \
                patch.object(preflight, "ensure_config", return_value=[]), \
                patch.object(preflight.os, "chdir"), patch.object(preflight.os, "execvp") as execute, \
                patch("builtins.print"):
            preflight.main()
            self.assertEqual(os.environ["PAPERCLIP_PUBLIC_URL"], valid()["PAPERCLIP_AUTH_PUBLIC_BASE_URL"])
            self.assertEqual(execute.call_args.args[0], "node")

    def test_invalid_environment_never_starts_the_server(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(preflight.os, "execvp") as execute, \
                patch.object(preflight, "check_storage") as storage, patch("builtins.print"):
            self.assertEqual(preflight.main(), 2)
            execute.assert_not_called()
            storage.assert_not_called()
