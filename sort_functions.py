import sys
import osmium

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
    sys.stderr.write("ERROR: unknown type {}\n".format(str(type(osm_object))))
    return "UNKNOWN"

