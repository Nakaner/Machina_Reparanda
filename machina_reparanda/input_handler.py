"""
© 2018 Michael Reichert

This file is part of Machina Reparanda.

osmi_simple_views is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

osmi_simple_views is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with osmi_simple_views. If not, see <http://www.gnu.org/licenses/>.
"""

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
