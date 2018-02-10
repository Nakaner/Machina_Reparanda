
import unittest

from machina_reparanda.configuration import Configuration
from implementations.nanowa import RevertImplementation
from machina_reparanda.mutable_osm_objects import MutableTagList, MutableWayNodeList, MutableRelationMemberList

from tests.mock_data_provider import MockDataProvider

def make_fake_source(configuration):
    fake_source = MockDataProvider(configuration, fake_data=True)
    revert_impl = RevertImplementation(configuration, fake_source)
    return fake_source, revert_impl

class NameRevertTestCase(unittest.TestCase):
    def setUp(self):
        self.config = Configuration({"user": "testUser", "uid": 12458, "password": "123secret"})
        self.data_source, self.revert_impl = make_fake_source(self.config)

    def test_revert_latest_version(self):
        code, latest = self.data_source.get_latest_version("way", 1)
        code, previous = self.data_source.get_version("way", 1, 2)
        result, cs = self.revert_impl.handle_obj(latest)
        self.assertEqual(previous.tags["building"], result.tags["building"])
        self.assertEqual(previous.tags["amenity"], result.tags["amenity"])
        self.assertEqual(previous.tags["religion"], result.tags["religion"])
        self.assertEqual(previous.tags["wikipedia"], result.tags["wikipedia"])
        self.assertEqual(previous.tags["source:geometry"], result.tags["source:geometry"])
        self.assertEqual(latest.nodes, result.nodes)
        self.assertEqual(result.version, 3)

    def test_already_reverted(self):
        code, v2 = self.data_source.get_version("way", 2, 2)
        code, v3 = self.data_source.get_version("way", 2, 3)
        code, v4 = self.data_source.get_version("way", 2, 4)
        code, latest = self.data_source.get_latest_version("way", 2)
        result, cs = self.revert_impl.solve_conflict(v2, latest, [3])
        self.assertIsNone(result)
        self.assertIsNone(cs)

    def test_simple_conflict(self):
        code, v2 = self.data_source.get_version("way", 3, 2)
        code, v3 = self.data_source.get_version("way", 3, 3)
        code, v4 = self.data_source.get_version("way", 3, 4)
        code, latest = self.data_source.get_latest_version("way", 3)
        result, cs = self.revert_impl.solve_conflict(v2, latest, [3])
        self.assertIsNotNone(result)
        self.assertEqual(len(cs), 1)
        self.assertIn(5, cs)
        self.assertEqual(v2.tags["building"], result.tags["building"])
        self.assertEqual(v2.tags["amenity"], result.tags["amenity"])
        self.assertEqual(v2.tags["religion"], result.tags["religion"])
        self.assertEqual(v2.tags["wikipedia"], result.tags["wikipedia"])
        self.assertEqual(v2.tags["source:geometry"], result.tags["source:geometry"])
        self.assertEqual(v4.tags["roof:colour"], result.tags["roof:colour"])
        self.assertEqual(latest.nodes, result.nodes)
        self.assertEqual(result.version, 4)

    def test_multi_version_conflict(self):
        """
        Revert edits of version 3 and 5 but preserve version 4. Version 5 is not harmful.
        """
        code, v2 = self.data_source.get_version("way", 4, 2)
        code, v3 = self.data_source.get_version("way", 4, 3)
        code, v4 = self.data_source.get_version("way", 4, 4)
        code, v5 = self.data_source.get_version("way", 4, 5)
        code, latest = self.data_source.get_latest_version("way", 4)
        result, cs = self.revert_impl.solve_conflict(v2, latest, [3, 5])
        self.assertIsNotNone(result)
        self.assertEqual(len(cs), 2)
        self.assertIn(5, cs)
        self.assertIn(25, cs)
        self.assertEqual(v2.tags["building"], result.tags["building"])
        self.assertEqual(v2.tags["amenity"], result.tags["amenity"])
        self.assertEqual(v2.tags["religion"], result.tags["religion"])
        self.assertEqual(v4.tags["source"], result.tags["source"])
        self.assertEqual(v4.tags["roof:colour"], result.tags["roof:colour"])
        self.assertEqual(latest.nodes, result.nodes)
        self.assertEqual(result.version, 5)
