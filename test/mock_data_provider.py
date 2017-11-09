import sys, os, inspect
import copy
import osmium

from .context import OsmApiClient, OsmApiResponse
from .context import MutableTagList, MutableWayNodeList

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

    def __init__(self, configuration, base_path=None):
        OsmApiClient.__init__(self, configuration)
        self.handler = MockDataHandler()
        if base_path is None:
            self.base_path = "{}/data/".format(self.__base_path__())
        else:
            self.base_path = base_path

    def get_latest_version(self, osm_type, osm_id):
        input_file = "{}/{}/{!s}.osm".format(self.base_path, osm_type, osm_id)
        self.handler.apply_file(input_file)
        return OsmApiResponse.EXISTS, self.handler.stored_way

    def get_version(self, osm_type, osm_id, version, fallback_if_redacted=True):
        input_file = "{}/{}/{!s}/{!s}.osm".format(self.base_path, osm_type, osm_id, version)
        self.handler.apply_file(input_file)
        return OsmApiResponse.EXISTS, self.handler.stored_way
