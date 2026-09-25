import base64
import unittest
from ivy_acceptance.paperclip_mac import environment


def fixture():
    key = base64.b64encode(b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20" + bytes(range(32))).decode()
    return {"host": "worker.example.ts.net", "username": "ivyworker", "workspace": "/Users/ivyworker/workspaces",
            "secret_id": "7c5f979c-78d4-4e29-9bba-e9c91e9076a2", "known_hosts": "worker.example.ts.net ssh-ed25519 " + key}


class PaperclipMacTests(unittest.TestCase):
    def test_native_config_has_pinned_secret_and_host_without_credentials(self):
        result = environment(**fixture())
        self.assertEqual(result["driver"], "ssh")
        self.assertTrue(result["config"]["strictHostKeyChecking"])
        self.assertIsNone(result["config"]["privateKey"])
        self.assertEqual(result["config"]["privateKeySecretRef"]["version"], 1)
        self.assertEqual(result["envVars"], {})

    def test_public_loopback_and_shell_hosts_refused(self):
        for host in ["8.8.8.8", "127.0.0.1", "example.com", "x;id", "-oProxyCommand=x", "x.ts.net.evil.com"]:
            with self.subTest(host=host), self.assertRaises(ValueError):
                environment(**{**fixture(), "host": host})

    def test_personal_root_and_mismatched_workspace_refused(self):
        for change in [{"username": "root"}, {"username": "tom"}, {"workspace": "/Users/tom/Build/ivy"},
                       {"workspace": "/Users/ivyworker/../tom"}, {"workspace": "/Users/ivyworker/.codex"},
                       {"workspace": "/Users/ivyworker"}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                environment(**{**fixture(), **change})

    def test_incorrect_host_pin_refused(self):
        for value in ["", "-----BEGIN OPENSSH PRIVATE KEY-----", fixture()["known_hosts"].replace("worker.example.ts.net", "*"),
                      fixture()["known_hosts"].replace("ssh-ed25519", "ssh-rsa"), "worker.example.ts.net ssh-ed25519 YQ=="]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                environment(**{**fixture(), "known_hosts": value})

    def test_invalid_secret_id_port_or_unpinned_version_refused(self):
        for change in [{"secret_id": "private-key"}, {"port": True}, {"port": 0}, {"port": 65536},
                       {"secret_version": "latest"}, {"secret_version": False}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                environment(**{**fixture(), **change})

    def test_nonstandard_port_requires_matching_host_pin(self):
        data = fixture()
        with self.assertRaises(ValueError):
            environment(**data, port=2222)
        data["known_hosts"] = data["known_hosts"].replace(data["host"], "[" + data["host"] + "]:2222")
        self.assertEqual(environment(**data, port=2222)["config"]["port"], 2222)
