from .context import RevertImplementation, Configuration

import unittest

from .mock_data_provider import MockDataProvider

class NameRevertTestCase(unittest.TestCase):
    def setUp(self):
        self.config = Configuration({"user": "testUser", "uid": 12458, "password": "123secret"})
        self.data_source = MockDataProvider(self.config)
        self.revert_impl = RevertImplementation(self.config, self.data_source)

    def test_revert_latest_version(self):
        code, latest = self.data_source.get_latest_version("way", 257006627)
        code, previous = self.data_source.get_version("way", 257006627, 3)
        result = self.revert_impl.handle_obj(latest)
        self.assertEqual(previous.tags["name"], result.tags["name"])
        self.assertEqual(result.version, 4)
