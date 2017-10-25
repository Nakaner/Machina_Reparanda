import sys
import requests
from sort_functions import type_to_int
from osm_xml_builder import OsmXmlBuilder


class OsmApiUploader():
    def __init__(self, configuration):
        self.user = configuration.user
        self.uid = configuration.bad_uid
        self.password = configuration.password
        self.comment = configuration.comment
        self.api_url = configuration.api_url
        self.xml_builder = OsmXmlBuilder(configuration.user)
        self.changeset = 0
        self.object_count = 0
        self.headers = {"User-Agent": "osmrevert-py/0.0.1", "Content-type": "text/xml"}
        self.max_object_count = 9999

    def open_changeset(self):
        xml = self.xml_builder.changeset(self.comment)
        sys.stdout.write(xml)
        url = "{}/changeset/create".format(self.api_url)
        sys.stderr.write("{} ...".format(url))
        data = xml.encode("utf-8")
        headers = self.headers.copy()
        headers["Content-Length"] = str(len(data))
        sys.stderr.write("Content-Length: {}\n".format(headers["Content-Length"]))
        r = requests.put(url, headers=headers, data=data, auth=(self.user, self.password), allow_redirects=True)
        sys.stderr.write("{}\n".format(r.status_code))
        if r.status_code == 200:
            self.changeset = int(r.text)
            sys.stderr.write("Changeset ID is {}\n".format(self.changeset))
            self.xml_builder.set_changeset(self.changeset)
        elif r.status_code == 400:
            sys.stderr.write("Programming ERROR: {}\n".format(r.text))
            exit(1)
        else:
            sys.stderr.write("Other ERROR: {}\n".format(r.text))

    def put_object(self, osm_type, osm_id, xml):
        sys.stdout.write(xml)
        url = "{}/{}/{}".format(self.api_url, osm_type, osm_id)
        sys.stderr.write("{} ...".format(url))
        data = xml.encode("utf-8")
        headers = self.headers.copy()
        headers["Content-Length"] = str(len(data))
        r = requests.put(url, headers=headers, data=data, auth=(self.user, "Su9phie0ai"))
        sys.stderr.write("{}\n".format(r.status_code))
        if r.status_code == 400:
            sys.stderr.write("Programming ERROR (Bad Request): {}\n".format(r.text))
        elif r.status_code == 404:
            sys.stderr.write("Programming ERROR (Not Found): {}\n".format(r.text))
        elif r.status_code == 412:
            sys.stderr.write("PRECONDITION FAILED: {}\n".format(r.text))
        elif r.status_code == 409:
            sys.stderr.write("CONFLICT: {}\n".format(r.text))
        elif r.status_code != 200:
            sys.stderr.write("Other ERROR: {}\n".format(r.text))

    def update_node(self, node):
        xml = self.xml_builder.node(node)
        self.put_object("node", node.id, xml)

    def update_way(self, way):
        xml = self.xml_builder.way(way)
        self.put_object("way", way.id, xml)

    def update_relation(self, relation):
        xml = self.xml_builder.relation(relation)
        self.put_object("relation", relation.id, xml)

    def handle_object(self, new_object):
        if new_object is None:
            return
        if self.changeset == 0:
            self.open_changeset()
        if self.object_count >= self.max_object_count:
            self.close_changeset()
            sys.stderr.write("Opening a new changeset\n")
            self.open_changeset()
        if type_to_int(new_object) == 1:
            self.update_node(new_object)
        elif type_to_int(new_object) == 2:
            self.update_way(new_object)
        elif type_to_int(new_object) == 3:
            self.update_relation(new_object)
        else:
            sys.stderr.write("ERROR: unkown type {}\n".format(type(new_object)))

    def close_changeset(self):
        sys.stdout.write("close CS\n")
        url = "{}/changeset/{}/close".format(self.api_url, self.changeset)
        sys.stderr.write("{} ...".format(url))
        r = requests.put(url, headers=self.headers, auth=(self.user, "Su9phie0ai"))
        sys.stderr.write("{}\n".format(r.status_code))
        if r.status_code == 200:
            sys.stderr.write("Changeset {} was successfully closed.\n".format(self.changeset))
            self.xml_builder.set_changeset(self.changeset)
        elif r.status_code == 404 or r.status_code == 405:
            sys.stderr.write("Programming ERROR: {}\n".format(r.text))
        elif r.status_code == 409:
            sys.stderr.write("CONFLICT: {}\n".format(r.text))
        else:
            sys.stderr.write("Other ERROR: {}\n".format(r.text))
        self.changeset = 0
