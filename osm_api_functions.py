import sys
import requests
import copy
import copyreg
import osmium
from enum import Enum
from sort_functions import obj_to_str
from mutable_osm_objects import *

api_url = "http://master.apis.dev.openstreetmap.org/api/0.6"

class ObjectCopyHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)

    def node(self, node):
        self.output_object = copy.deepcopy(osmium.osm.mutable.Node(node, tags=MutableTagList(node.tags)))

    def way(self, way):
        self.output_object = copy.deepcopy(osmium.osm.mutable.Way(way, tags=MutableTagList(way.tags), nodes=MutableWayNodeList(way.nodes)))

    def relation(self, relation):
        self.output_object = copy.deepcopy(osmium.osm.mutable.Relation(relation, tags=MutableTagList(relation.tags), members=MutableRelationMemberList(relation.members)))


class OsmApiResponse(Enum):
    NOT_FOUND = 0
    EXISTS = 1
    DELETED = 2
    REDACTED = 3
    TOO_MANY = 4
    ERROR = 5

class OsmApiClient:
    def __init__(self, osm_object):
        self.id = osm_object.id
        self.type = obj_to_str(osm_object)
        self.url = ""
        self.headers = {'user-agent': 'osmrevert-py/0.0.1'}

    def get_version(self, version):
        self.url = "{}/{}/{}/{}".format(api_url, self.type, self.id, version)
        sys.stderr.write("GET {} ...".format(self.url))
        r = requests.get(self.url, headers=self.headers)
        sys.stderr.write(" {}\n".format(r.status_code))
        if r.status_code == 403: # forbidden – redacted version
            if version > 1:
                get_version(osm_type, obj_id, version - 1)
                return
            else:
                self.status = OsmApiResponse.REDACTED
                sys.stderr.write("manual action necessary because all previous versions are redacted for {} {}\n".format(obj_to_str(osm_type), obj_id))
                return
        elif r.status_code != 200: # other error
            self.status = OsmApiResponse.ERROR
            sys.stderr.write("API returned error {} for request {}\n".format(r.status_code, self.url))
            return
    
        # parse result
        data = r.content
        handler = ObjectCopyHandler()
        handler.apply_buffer(data, ".osm")
        self.retrieved_object = handler.output_object
        self.status = OsmApiResponse.EXISTS

    def get_latest_version(self):
        self.url = "{}/{}/{}".format(api_url, self.type, self.id)
        sys.stderr.write("GET {} ...".format(self.url))
        r = requests.get(self.url, headers=self.headers)
        sys.stderr.write(" {}\n".format(r.status_code))
        if r.status_code == 404:
            self.status = OsmApiResponse.NOT_FOUND
        elif r.status_code == 410:
            self.status = OsmApiResponse.DELETED
        elif r.status_code != 200:
            self.status = OsmApiResponse.ERROR
        else:
            data = r.content
            handler = ObjectCopyHandler()
            handler.apply_buffer(data, ".osm")
            self.retrieved_object = handler.output_object
            self.status = OsmApiResponse.EXISTS

