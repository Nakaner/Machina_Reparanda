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

import osmium

from .revert_exceptions import OSMException

def type_to_int(osm_object):
    if isinstance(osm_object, osmium.osm.Node) or isinstance(osm_object, osmium.osm.mutable.Node):
        return 1
    if isinstance(osm_object, osmium.osm.Way) or isinstance(osm_object, osmium.osm.mutable.Way):
        return 2
    if isinstance(osm_object, osmium.osm.Relation) or isinstance(osm_object, osmium.osm.mutable.Relation):
        return 3
    return 4


def equal_type_id(lhs, rhs):
    return type_to_int(lhs) == type_to_int(rhs) and lhs.id == rhs.id


def obj_to_str(osm_object):
    type_id = type_to_int(osm_object)
    if type_id == 1:
        return "node"
    if type_id == 2:
        return "way"
    if type_id == 3:
        return "relation"
    raise OSMException("unknown type {}\n".format(str(type(osm_object))))
