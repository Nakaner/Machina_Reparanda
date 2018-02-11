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

import logging
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
        logging.debug(xml)
        url = "{}/changeset/create".format(self.api_url)
        data = xml.encode("utf-8")
        headers = self.headers.copy()
        headers["Content-Length"] = str(len(data))
        r = requests.put(url, headers=headers, data=data, auth=(self.user, self.password), allow_redirects=True)
        logging.debug("PUT {} {}".format(url, r.status_code))
        if r.status_code == 200:
            self.changeset = int(r.text)
            logging.info("Changeset ID is {}".format(self.changeset))
            self.xml_builder.set_changeset(self.changeset)
        elif r.status_code == 400:
            logging.critical("Programming ERROR: {}".format(r.text))
            exit(1)
        else:
            logging.error("Other ERROR: {}".format(r.text))

    def put_object(self, osm_type, osm_id, xml):
        logging.debug(xml)
        url = "{}/{}/{}".format(self.api_url, osm_type, osm_id)
        data = xml.encode("utf-8")
        headers = self.headers.copy()
        headers["Content-Length"] = str(len(data))
        r = requests.put(url, headers=headers, data=data, auth=(self.user, self.password))
        logging.debug("PUT {} {}".format(url, r.status_code))
        if r.status_code == 400:
            logging.error("Programming ERROR (Bad Request): {}".format(r.text))
        elif r.status_code == 404:
            logging.error("Programming ERROR (Not Found): {}".format(r.text))
        elif r.status_code == 412:
            logging.error("PRECONDITION FAILED: {}".format(r.text))
        elif r.status_code == 409:
            logging.error("CONFLICT: {}".format(r.text))
        elif r.status_code != 200:
            logging.error("Other ERROR: {}".format(r.text))

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
            logging.debug("would upload:{} {} version {} with following tags:\n{}".format(obj_to_str(new_object), obj.id, obj.version, obj.tags))
            return
        if self.changeset == 0:
            self.open_changeset()
        if self.object_count >= self.max_object_count:
            self.close_changeset()
            logging.info("Opening a new changeset")
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
            logging.critical("ERROR: unkown type {}".format(type(new_object)))

    def comment_changeset(self, cs_id, comment):
        """
        Post a changeset comment to a changeset.

        Args:
            cs_id (int): ID of the changeset to be commented
            comment (str): comment to be posted
        """
        if self.dryrun:
            logging.info("would comment changeset {} with \"{}\"".format(cs_id, comment))
            return
        payload = {"text": comment}
        url = "{}/changeset/{}/comment".format(self.api_url, cs_id)
        r = requests.post(url, data=payload, headers=self.headers_comments, auth=(self.user, self.password))
        logging.debug("POST comment on {} {}".format(url, r.status_code))
        logging.debug(r.text)

    def make_changeset_comment_text(self):
        text = "This changeset reverts some or all edits made in the following changeset: "
        ids = ", ".join(str(cs_id) for cs_id in self.reverted_changesets)
        text += ids
        return text

    def close_changeset(self):
        if self.changeset == 0 or self.dryrun:
            return
        url = "{}/changeset/{}/close".format(self.api_url, self.changeset)
        logging.debug("PUT {} {}".format(url, r.status_code))
        r = requests.put(url, headers=self.headers, auth=(self.user, self.password))
        if r.status_code == 200:
            logging.info("Changeset {} was successfully closed.".format(self.changeset))
            self.xml_builder.set_changeset(self.changeset)
        elif r.status_code == 404 or r.status_code == 405:
            logging.error("Programming ERROR: {}".format(r.text))
        elif r.status_code == 409:
            logging.error("CONFLICT: {}".format(r.text))
        else:
            logging.error("Other ERROR: {}".format(r.text))
        # comment the changeset
        self.comment_changeset(self.changeset, self.make_changeset_comment_text())
        # reset
        self.used_changesets.add(self.changeset)
        self.changeset = 0
        self.reverted_changesets = set()
