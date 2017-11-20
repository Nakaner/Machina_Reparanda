import copy
import osmium
from machina_reparanda.mutable_osm_objects import MutableTagList, MutableRelationMemberList, MutableWayNodeList, MutableLocation


class InputHandler(osmium.SimpleHandler):
    def __init__(self, object_list):
        osmium.SimpleHandler.__init__(self)
        self.object_list = object_list

    def add_to_list(self, mutable_object):
        self.object_list.append(copy.deepcopy(mutable_object))
        #self.object_list.append(mutable_object)

    def node(self, node):
        self.add_to_list(osmium.osm.mutable.Node(node, tags=MutableTagList(node.tags), location=MutableLocation(node.location)))

    def way(self, way):
        self.add_to_list(osmium.osm.mutable.Way(way, tags=MutableTagList(way.tags), nodes=MutableWayNodeList(way.nodes)))

    def relation(self, relation):
        self.add_to_list(osmium.osm.mutable.Relation(relation, tags=MutableTagList(relation.tags), members=MutableRelationMemberList(relation.members)))
