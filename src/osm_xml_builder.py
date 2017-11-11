import sys


# TODO escape strings
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
            sys.stderr.write("Programming ERROR\n")
            # TODO throw exception

    def add_header(self):
        self.buffer = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        self.buffer += "<osm version=\"0.6\">\n"

    def finalize(self):
        self.buffer += "</osm>\n"

    def add_key_value(self, key, value):
        self.buffer += "    <tag k=\"{}\" v=\"{}\"/>\n".format(key, value)

    def add_tag(self, tag):
        self.add_key_value(tag.k, tag.v)

    def add_tags(self, tag_list):
        for key, value in tag_list.items():
            self.add_key_value(key, value)

    def add_node_ref(self, node_ref):
        self.buffer += "    <nd ref=\"{}\"/>\n".format(node_ref.ref)

    def add_way_node_list(self, way_node_list):
        for nd_ref in way_node_list:
            self.add_node_ref(nd_ref)

    def add_relation_member(self, member):
        self.buffer += "    <member type=\"{}\" ref=\"{}\" role=\"{}\"/>\n".format(member.type, member.ref, member.role)

    def add_relation_member_list(self, relation_members):
        for member in relation_members:
            self.add_relation_member(member)

    def changeset(self, comment):
        self.buffer = ""
        self.add_header()
        self.buffer += "  <changeset>\n"
        self.add_key_value("created_by", self.configuration.user_agent)
        #TODO shorten comment
        self.add_key_value("comment", comment)
        self.add_key_value("bot", "yes")
        self.add_key_value("reverting", "yes")
        self.buffer += "  </changeset>\n"
        self.finalize()
        return self.buffer

    def node(self, node):
        self.reset()
        self.add_header()
        self.buffer += "  <node id=\"{}\" changeset=\"{}\" version=\"{}\" visible=\"true\" user=\"{}\">\n".format(node.id, self.changeset_id, node.version, self.user)
        self.add_tags(node.tags)
        self.buffer += "  </node>\n"
        self.finalize()
        return self.buffer

    def way(self, way):
        self.reset()
        self.add_header()
        self.buffer += "  <way id=\"{}\" changeset=\"{}\" version=\"{}\" visible=\"true\" user=\"{}\">\n".format(way.id, self.changeset_id, way.version, self.user)
        self.add_way_node_list(way.nodes)
        self.add_tags(way.tags)
        self.buffer += "  </way>\n"
        self.finalize()
        return self.buffer

    def relation(self, relation):
        self.reset()
        self.add_header()
        self.buffer += "  <relation id=\"{}\" changeset=\"{}\" version=\"{}\" visible=\"true\" user=\"{}\">\n".format(relation.id, self.changeset_id, relation.version, self.user)
        self.add_relation_member_list(relation.members)
        self.add_tags(relation.tags)
        self.buffer += "  </relation>\n"
        self.finalize()
        return self.buffer

