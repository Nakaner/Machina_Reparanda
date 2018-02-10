import sys
import requests
from .sort_functions import type_to_int, obj_to_str
from .osm_xml_builder import OsmXmlBuilder


class OsmApiUploader():
    def __init__(self, configuration):
        self.user = configuration.user #: user to be used for upload
        self.password = configuration.password #: password to be used for upload
        self.comment = configuration.comment #: changeset comment to be used for upload
        self.api_url = configuration.api_url #: API endpoint to be used for upload
        self.dryrun = configuration.dryrun
        self.xml_builder = OsmXmlBuilder(configuration) #: instance of OsmXmlBuilder class
        self.changeset = 0 #: ID of currently open changeset
        self.used_changesets = set() #: IDs of changesets used by this instance
        self.object_count = 0 #: number of objects written to this changeset
        self.reverted_changesets = set() #: set of reverted changesets
        self.headers = {"User-Agent": configuration.user_agent, "Content-type": "text/xml"} #: HTTP headers
        self.headers_comments = {"User-Agent": configuration.user_agent, "Content-type": "application/x-www-form-urlencoded"} #: HTTP headers for changeset discussions API
        #TODO retriev size limit of changesets from the API capabilities
        self.max_object_count = 9999 #: maximum number of objects to be written into one changeset
        if configuration.reuse_changeset > 0:
            self.changeset = configuration.reuse_changeset
            self.xml_builder.set_changeset(configuration.reuse_changeset)

    def open_changeset(self):
        xml = self.xml_builder.changeset(self.comment)
        sys.stdout.write(xml)
        url = "{}/changeset/create".format(self.api_url)
        sys.stderr.write("PUT {} ...".format(url))
        data = xml.encode("utf-8")
        headers = self.headers.copy()
        headers["Content-Length"] = str(len(data))
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
        sys.stderr.write("PUT {} ...".format(url))
        data = xml.encode("utf-8")
        headers = self.headers.copy()
        headers["Content-Length"] = str(len(data))
        r = requests.put(url, headers=headers, data=data, auth=(self.user, self.password))
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

    def handle_object(self, new_object, changesets):
        if new_object is None:
            return
        if self.dryrun:
            obj = new_object
            sys.stderr.write("\nwould upload:\n{} {} version {}:\n{}\n".format(obj_to_str(new_object), obj.id, obj.version, obj.tags))
            return
        if self.changeset == 0:
            self.open_changeset()
        if self.object_count >= self.max_object_count:
            self.close_changeset()
            sys.stderr.write("Opening a new changeset\n")
            self.open_changeset()
        for cs in changesets:
            self.reverted_changesets.add(cs)
        if type_to_int(new_object) == 1:
            self.update_node(new_object)
        elif type_to_int(new_object) == 2:
            self.update_way(new_object)
        elif type_to_int(new_object) == 3:
            self.update_relation(new_object)
        else:
            sys.stderr.write("ERROR: unkown type {}\n".format(type(new_object)))

    def comment_changeset(self, cs_id, comment):
        """
        Post a changeset comment to a changeset.

        Args:
            cs_id (int): ID of the changeset to be commented
            comment (str): comment to be posted
        """
        if self.dryrun:
            sys.stderr.write("would comment changeset {} with\n\"{}\"\n".format(cs_id, comment))
            return
        payload = {"text": comment}
        url = "{}/changeset/{}/comment".format(self.api_url, cs_id)
        sys.stderr.write("POST comment on {} ... ".format(url))
        r = requests.post(url, data=payload, headers=self.headers_comments, auth=(self.user, self.password))
        sys.stderr.write("{}\n".format(r.status_code))
        sys.stderr.write(r.text)

    def make_changeset_comment_text(self):
        text = "This changeset reverts some or all edits made in the following changeset: "
        ids = ", ".join(str(cs_id) for cs_id in self.reverted_changesets)
        text += ids
        return text

    def close_changeset(self):
        if self.changeset == 0 or self.dryrun:
            return
        sys.stdout.write("close CS\n")
        url = "{}/changeset/{}/close".format(self.api_url, self.changeset)
        sys.stderr.write("PUT {} ...".format(url))
        r = requests.put(url, headers=self.headers, auth=(self.user, self.password))
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
        # comment the changeset
        self.comment_changeset(self.changeset, self.make_changeset_comment_text())
        # reset
        self.used_changesets.add(self.changeset)
        self.changeset = 0
        self.reverted_changesets = set()
