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

    def test_already_reverted(self):
        code, v5 = self.data_source.get_version("way", 33072216, 5)
        code, v6 = self.data_source.get_version("way", 33072216, 6)
        code, v7 = self.data_source.get_version("way", 33072216, 7)
        code, latest = self.data_source.get_latest_version("way", 33072216)
        result = self.revert_impl.solve_conflict(v5, latest, [6])
        self.assertIsNone(result)

    def test_real_conflict(self):
        fake_source = MockDataProvider(self.config, fake_data=True)
        revert_impl = RevertImplementation(self.config, fake_source)
        code, v5 = fake_source.get_version("way", 33072216, 5)
        code, v6 = fake_source.get_version("way", 33072216, 6)
        code, latest = fake_source.get_latest_version("way", 33072216)
        result = revert_impl.solve_conflict(v5, latest, [6])
        self.assertIsNotNone(result)
        self.assertEqual(v5.tags["name"], result.tags["name"])
        self.assertEqual(result.version, 7)
        self.assertIn("surface", result.tags)
