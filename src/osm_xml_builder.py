from xml.sax import saxutils

from revert_exceptions import TagInvalidException, ProgrammingError


class OsmXmlBuilder:
    def __init__(self, configuration):
        self.buffer = ""
        self.user = configuration.user
        self.user_agent = configuration.user_agent
        self.changeset_id = 0

    def set_changeset(self, changeset):
        self.changeset_id = changeset

    def reset(self):
        self.buffer = ""
        if self.changeset_id == 0:
            raise ProgrammingError("When cleaning the buffer to create a new object, the changeset ID must not be 0.")

    def add_header(self):
        self.buffer = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        self.buffer += "<osm version=\"0.6\">\n"

    def finalize(self):
        self.buffer += "</osm>\n"

    def check_and_escape(self, data):
        """
        Check the length of an key or value, escape it for XML transport and
        surround it by quotes.

        Args:
            data (str): key/value to be escaped

        Returns:
            str: quoted and escaped key/value

        Raises:
            TagInvalidException: If the key/value to be escaped is longer than
            255 characters.
        """
        if len(data) > 255:
            raise TagInvalidException(data, "Key or value is too long.")
        return saxutils.quoteattr(data)

    def add_key_value(self, key, value):
        k = self.check_and_escape(key)
        v = self.check_and_escape(value)
        self.buffer += "    <tag k={} v={}/>\n".format(k, v)

    def add_tag(self, tag):
        self.add_key_value(tag.k, tag.v)

    def add_tags(self, tag_list):
        for key, value in tag_list.items():
            self.add_key_value(key, value)

    def add_node_ref(self, node_ref):
        ndr = saxutils.quoteattr(str(node_ref.ref))
        self.buffer += "    <nd ref={}/>\n".format(ndr)

    def add_way_node_list(self, way_node_list):
        for nd_ref in way_node_list:
            self.add_node_ref(nd_ref)

    def add_relation_member(self, member):
        mtype = saxutils.quoteattr(member.type)
        mref = saxutils.quoteattr(str(member.ref))
        mrole = saxutils.quoteattr(member.role)
        self.buffer += "    <member type={} ref={} role={}/>\n".format(mtype, mref, mrole)

    def add_relation_member_list(self, relation_members):
        for member in relation_members:
            self.add_relation_member(member)

    def changeset(self, comment):
        self.buffer = ""
        self.add_header()
        self.buffer += "  <changeset>\n"
        self.add_key_value("created_by", self.configuration.user_agent)
        #TODO shorten comment
        if len(comment) >= 254:
            self.add_key_value("comment", comment[0:255])
        else:
            self.add_key_value("comment", comment)
        self.add_key_value("bot", "yes")
        self.add_key_value("reverting", "yes")
        self.buffer += "  </changeset>\n"
        self.finalize()
        return self.buffer

    def _visible_to_str(self, visibility):
        """
        Convert visible attribute of an OSM object to XML-quoted, lowercase string of either ``true`` or ``false``

        Args:
            visibility (boolean): return value of OSMObject.visible

        Returns:
            str
        """
        if visibility:
            return "\"true\""
        return "\"false\""

    def node(self, node):
        self.reset()
        self.add_header()
        self.buffer += "  <node id=\"{}\" changeset=\"{}\" version=\"{}\" visible={} user=\"{}\">\n".format(node.id, self.changeset_id, node.version, self._visible_to_str(node.visible), self.user)
        self.add_tags(node.tags)
        self.buffer += "  </node>\n"
        self.finalize()
        return self.buffer

    def way(self, way):
        self.reset()
        self.add_header()
        self.buffer += "  <way id=\"{}\" changeset=\"{}\" version=\"{}\" visible={} user=\"{}\">\n".format(way.id, self.changeset_id, way.version, self._visible_to_str(way.visible), self.user)
        self.add_way_node_list(way.nodes)
        self.add_tags(way.tags)
        self.buffer += "  </way>\n"
        self.finalize()
        return self.buffer

    def relation(self, relation):
        self.reset()
        self.add_header()
        self.buffer += "  <relation id=\"{}\" changeset=\"{}\" version=\"{}\" visible={} user=\"{}\">\n".format(relation.id, self.changeset_id, relation.version, self._visible_to_str(relation.visible), self.user)
        self.add_relation_member_list(relation.members)
        self.add_tags(relation.tags)
        self.buffer += "  </relation>\n"
        self.finalize()
        return self.buffer
