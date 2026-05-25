from django.test import SimpleTestCase

from tracker.dealhost import (
    build_dealhost_runtime_manifest,
    dealhost_hosts_from_env,
    dealhost_origins_from_env,
)


class DealhostRuntimeTests(SimpleTestCase):
    def test_dealhost_hosts_and_origins_from_env(self):
        environ = {
            'DEALHOST_APP_URL': 'https://pybehaviorlog.example.com/app',
            'DEALHOST_ALLOWED_HOSTS': 'extra.example.com, pybehaviorlog.example.com',
        }
        self.assertEqual(
            dealhost_hosts_from_env(environ),
            ['extra.example.com', 'pybehaviorlog.example.com'],
        )
        self.assertEqual(
            dealhost_origins_from_env(environ),
            ['https://pybehaviorlog.example.com', 'https://extra.example.com'],
        )

    def test_dealhost_manifest_is_safe_without_sdk(self):
        manifest = build_dealhost_runtime_manifest(
            {
                'DEALHOST_ENABLED': '1',
                'DEALHOST_APP_URL': 'https://pybehaviorlog.example.com',
                'PORT': '9000',
                'PYBEHAVIORLOG_CACHE_BACKEND': 'locmem',
            }
        )
        self.assertTrue(manifest['enabled'])
        self.assertEqual(manifest['port'], '9000')
        self.assertEqual(manifest['cache_backend'], 'locmem')
        self.assertFalse(manifest['sdk']['available'])
