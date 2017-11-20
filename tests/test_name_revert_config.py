
import unittest

from machina_reparanda.configuration import Configuration
from implementations.revert_implementation import RevertImplementation
from machina_reparanda.mutable_osm_objects import MutableTagList, MutableWayNodeList, MutableRelationMemberList

from tests.mock_data_provider import MockDataProvider

def make_fake_source(configuration):
    fake_source = MockDataProvider(configuration, fake_data=True)
    revert_impl = RevertImplementation(configuration, fake_source)
    return fake_source, revert_impl

class NameRevertTestCase(unittest.TestCase):
    def setUp(self):
        self.config = Configuration({"user": "testUser", "uid": 12458, "password": "123secret"})
        self.data_source = MockDataProvider(self.config)
        self.revert_impl = RevertImplementation(self.config, self.data_source)

    def test_revert_latest_version(self):
        code, latest = self.data_source.get_latest_version("way", 257006627)
        code, previous = self.data_source.get_version("way", 257006627, 3)
        result, cs = self.revert_impl.handle_obj(latest)
        self.assertEqual(previous.tags["name"], result.tags["name"])
        self.assertEqual(result.version, 4)

    def test_already_reverted(self):
        code, v5 = self.data_source.get_version("way", 33072216, 5)
        code, v6 = self.data_source.get_version("way", 33072216, 6)
        code, v7 = self.data_source.get_version("way", 33072216, 7)
        code, latest = self.data_source.get_latest_version("way", 33072216)
        result, cs = self.revert_impl.solve_conflict(v5, latest, [6])
        self.assertIsNone(result)
        self.assertIsNone(cs)

    def test_real_conflict(self):
        fake_source, revert_impl = make_fake_source(self.config)
        code, v5 = fake_source.get_version("way", 33072216, 5)
        code, v6 = fake_source.get_version("way", 33072216, 6)
        code, latest = fake_source.get_latest_version("way", 33072216)
        result, cs = revert_impl.solve_conflict(v5, latest, [6])
        self.assertIsNotNone(result)
        self.assertEqual(len(cs), 1)
        self.assertIn(52071384, cs)
        self.assertEqual(v5.tags["name"], result.tags["name"])
        self.assertEqual(result.version, 7)
        self.assertIn("surface", result.tags)

    def test_conflict_multiple_not_to_revert_changesets(self):
        fake_source, revert_impl = make_fake_source(self.config)
        code, v1 = fake_source.get_version("way", 501700, 1)
        code, latest = fake_source.get_latest_version("way", 501700)
        result, cs = revert_impl.solve_conflict(v1, latest, [2])
        self.assertIsNotNone(result)
        self.assertEqual(v1.tags["name"], result.tags["name"])
        self.assertEqual(result.version, 4)
        self.assertEqual(len(cs), 1)
        self.assertIn(108213, cs)
