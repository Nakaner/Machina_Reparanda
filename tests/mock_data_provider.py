import os
import inspect
import copy
import osmium

from machina_reparanda import OsmApiClient, OsmApiResponse
from machina_reparanda import MutableTagList, MutableWayNodeList


class MockDataHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)

    def node(self, node):
        self.stored_node = copy.deepcopy(osmium.osm.mutable.Node(node, tags=MutableTagList(node.tags)))

    def way(self, way):
        self.stored_way = copy.deepcopy(osmium.osm.mutable.Way(way, tags=MutableTagList(way.tags), nodes=MutableWayNodeList(way.nodes)))


class MockDataProvider(OsmApiClient):
    def __base_path__(self):
        return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    def __get_path__(self, osm_type, osm_id, osm_version=None):
        base = self.base_path
        if self.fake_data:
            base += "/fake/"
        if osm_version is None:
            return "{}/{}/{}.osm".format(base, osm_type, osm_id)
        return "{}/{}/{}/{}.osm".format(base, osm_type, osm_id, osm_version)

    def __init__(self, configuration, **kwargs):
        OsmApiClient.__init__(self, configuration)
        self.handler = MockDataHandler()
        self.fake_data = False
        if "fake_data" in kwargs:
            self.fake_data = kwargs["fake_data"]
        self.base_path = "{}/data/".format(self.__base_path__())
        if "base_path" in kwargs:
            self.base_path = kwargs["base_path"]

    def get_latest_version(self, osm_type, osm_id):
        input_file = self.__get_path__(osm_type, osm_id)
        self.handler.apply_file(input_file)
        return OsmApiResponse.EXISTS, self.handler.stored_way

    def get_version(self, osm_type, osm_id, version, fallback_if_redacted=True):
        input_file = self.__get_path__(osm_type, osm_id, version)
        self.handler.apply_file(input_file)
        return OsmApiResponse.EXISTS, self.handler.stored_way
