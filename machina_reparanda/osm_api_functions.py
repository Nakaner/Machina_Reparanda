"""
© 2018 Michael Reichert

This file is part of Machina Reparanda.

Machina Reparanda is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

Machina Reparanda is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Machina Reparanda. If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import requests
import copy
import osmium
from enum import Enum
from machina_reparanda.mutable_osm_objects import MutableTagList, MutableWayNodeList, MutableRelationMemberList, MutableLocation
from machina_reparanda.sort_functions import type_to_int


class ObjectCopyHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.objects = []

    def get_object(self):
        return self.objects[0]

    def node(self, node):
        self.objects.append(copy.deepcopy(osmium.osm.mutable.Node(node, tags=MutableTagList(node.tags), location=MutableLocation(node.location))))

    def way(self, way):
        self.objects.append(copy.deepcopy(osmium.osm.mutable.Way(way, tags=MutableTagList(way.tags), nodes=MutableWayNodeList(way.nodes))))

    def relation(self, relation):
        self.objects.append(copy.deepcopy(osmium.osm.mutable.Relation(relation, tags=MutableTagList(relation.tags), members=MutableRelationMemberList(relation.members))))


class OsmApiResponse(Enum):
    NOT_FOUND = 0
    EXISTS = 1
    DELETED = 2
    REDACTED = 3
    TOO_MANY = 4
    ERROR = 5
    REDACTED_FALLBACK = 6


class OsmApiClient:
    def __init__(self, configuration):
        self.api_url = configuration.api_url
        self.headers = {'user-agent': configuration.user_agent}

    def get_history(self, osm_type, osm_id):
        url = "{}/{}/{}/history".format(self.api_url, osm_type, osm_id)
        r = requests.get(url, headers=self.headers)
        logging.debug("GET {} {}".format(url, r.status_code))
        if r.status_code == 403:  # forbidden – redacted version
            if version > 1 and fallback_if_redacted:
                return OsmApiResponse.REDACTED_FALLBACK, self.get_version(osm_type, osm_id, version - 1, fallback_if_redacted)
            else:
                logging.warning("Manual action necessary because all previous versions are redacted for {} {}".format(osm_type, osm_id))
                return OsmApiResponse.REDACTED, None
        elif r.status_code != 200:  # other error
            return OsmApiResponse.ERROR, None

        # parse result
        data = r.content
        handler = ObjectCopyHandler()
        handler.apply_buffer(data, ".osm")
        handler.objects.sort(key=lambda obj: (type_to_int(obj), obj.id, obj.version))
        return OsmApiResponse.EXISTS, handler.objects

    def get_version(self, osm_type, osm_id, version, fallback_if_redacted=True):
        url = "{}/{}/{}/{}".format(self.api_url, osm_type, osm_id, version)
        r = requests.get(url, headers=self.headers)
        logging.debug("GET {} {}".format(url, r.status_code))
        if r.status_code == 403:  # forbidden – redacted version
            if version > 1 and fallback_if_redacted:
                return OsmApiResponse.REDACTED_FALLBACK, self.get_version(osm_type, osm_id, version - 1, fallback_if_redacted)
            else:
                logging.warning("Manual action necessary because all previous versions are redacted for {} {}".format(osm_type, osm_id))
                return OsmApiResponse.REDACTED, None
        elif r.status_code != 200:  # other error
            return OsmApiResponse.ERROR, None

        # parse result
        data = r.content
        handler = ObjectCopyHandler()
        handler.apply_buffer(data, ".osm")
        return OsmApiResponse.EXISTS, handler.get_object()

    def get_latest_version(self, osm_type, osm_id):
        url = "{}/{}/{}".format(self.api_url, osm_type, osm_id)
        r = requests.get(url, headers=self.headers)
        logging.debug("GET {} {}".format(url, r.status_code))
        if r.status_code == 404:
            return OsmApiResponse.NOT_FOUND, None
        elif r.status_code == 410:
            return OsmApiResponse.DELETED, None
        elif r.status_code != 200:
            return OsmApiResponse.ERROR, None
        else:
            data = r.content
            handler = ObjectCopyHandler()
            handler.apply_buffer(data, ".osm")
            return OsmApiResponse.EXISTS, handler.get_object()
