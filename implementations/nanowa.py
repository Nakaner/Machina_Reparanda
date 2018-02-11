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


import sys
from machina_reparanda.abstract_revert_implementation import AbstractRevertImplementation
from machina_reparanda.sort_functions import obj_to_str
from machina_reparanda.osm_api_functions import OsmApiResponse


def get_next_greater_or_equal_element(the_list, current_value):
    for i in range(0, len(the_list)):
        if the_list[i] >= current_value:
            return i
    return len(the_list)


class RevertImplementation(AbstractRevertImplementation):
    """
    This implementation was used to revert the deletions of the following tags which were spread over
    over hundret changesets by one single user and mixed with good edits: wikipedia=*, wikidata=*,
    source=*, wikipedia:*=*, source:*=*, wikidata:*=*.

    The implementation also contains an automatic conflict solution because it only reverts changes
    on tags, not on coordinates and members. There are also unit tests for this implementation in the
    test directory.
    """

    def __init__(self, configuration, api_client):
        super().__init__(configuration, api_client)

    def handle_v1_object(self, obj):
        sys.stderr.write("Ignoring {} {} version {} because it is the only version available.\n".format(obj_to_str(obj), obj.id, obj.version))
        return None, None

    def is_malicious_change(self, prev_version, this_version):
        for k in ["wikipedia", "wikidata", "source", "source:geometry"]:
            if k in prev_version.tags and k not in this_version.tags:
                # if one version does not contain a name tag, ignore the change
                return True
            for tk, tv in prev_version.tags.items():
                if tk.startswith("{}:".format(k)) and tk not in this_version.tags:
                    return True
        return False

    def revert(self, v1, v2):
        sys.stderr.write("Reverting change of {} {} version {}\n".format(obj_to_str(v2), v2.id, v2.version))
        for k in ["wikipedia", "wikidata", "source", "source:geometry"]:
            if k in v1.tags and k not in v2.tags:
                v2.tags[k] = v1.tags[k]
            for tk, tv in v1.tags.items():
                if tk.startswith("{}:".format(k)) and tk not in v2.tags:
                    v2.tags[tk] = tv
        return v2

    def do_changes(self, v1, v2, existing_changes):
        for k in ["wikipedia", "wikidata", "source", "source:geometry"]:
            if k in v1.tags and k not in v2.tags:
                existing_changes[k] = v1.tags[k]
            for tk, tv in v1.tags.items():
                if tk.startswith("{}:".format(k)) and tk not in v2.tags:
                    existing_changes[tk] = tv

    def apply_good_changes(self, v1, v2, existing_changes):
        for k in ["wikipedia", "wikidata", "source", "source:geometry"]:
            if k in v2.tags:
                existing_changes[k] = v2.tags[k]
            for tk, tv in v2.tags.items():
                if tk.startswith("{}:".format(k)):
                    existing_changes[tk] = tv

    def has_a_interesting_tag(self, taglist, keylist):
        """
        Check if a instance of osmium.osm.TagList or MutableTagList contains a least one of the
        strings in keylist.

        Args:
            taglist (MutableTagList): taglist of the OSM object
            keylist (list of str): list of keys

        Returns:
            bool
        """
        f = list(filter(lambda x: x in taglist, keylist))
        return len(f) > 0

    def handle_obj(self, obj):
        # get latest version
        obj_type = obj_to_str(obj)
        response, latest_version = self.api_client.get_latest_version(obj_type, obj.id)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            return None, None
        # get previous version
        response, prev_version = self.api_client.get_version(obj_type, obj.id, obj.version - 1)
        if response == OsmApiResponse.REDACTED:
            # all previous versions are redacted
            return self.handle_v1_object(obj)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            sys.stderr.write("Unable to revert {} {} version {} because no previous version available (deleted, not found or API error)\n".format(obj_to_str(obj), obj.id, obj.version))
            return None, None
        if self.is_malicious_change(prev_version, obj):
            if latest_version.version > obj.version:
                # conflict
                sys.stderr.write("CONFLICT (will be solved automatically): {} {}, could provide version {}, got version {} from API\n".format(obj_to_str(obj), obj.id, obj.version, latest_version.version))
                return self.solve_conflict(prev_version, latest_version, [obj.version])
            return self.revert(prev_version, obj), {obj.changeset}
        return None, None

    def has_tag_changed(self, old_object, new_object, key):
        """
        Check if the value of a given key has changed between the two versions.

        Args:
            old_object (osmium.mutable.osm.OSMObject): older version
            new_object (osmium.mutable.osm.OSMObject): new version
            key (string): key to check

        Returns:
            bool: has the key changed
            string: new value, empty if the key has been deleted
        """
        if key not in old_object.tags and key in new_object.tags:
            return True, new_object.tags[key]
        if key in old_object.tags and key not in new_object.tags:
            return True, ""
        if key not in old_object.tags and key not in new_object.tags:
            return False, ""
        if old_object.tags[key] == new_object.tags[key]:
            return False, new_object.tags[key]
        return True, new_object.tags[key]

    def solve_conflict(self, oldest_version, latest_version, bad_versions, **kwargs):
        """
        Check if all versions of an object from from_version to the latest version
        contain only "good" changes.

        Args:
            oldest_version (osmium.mutable.osm.OSMObject): oldest version of the object to be
            scanned. This is usually the version before the first version to be reverted.
            latest_version (osmium.mutable.osm.OSMObject): latest version of the object (usually retrieved from the API)
            bad_versions (list of int): list of version numbers which are considered bad

        Kwargs:
            initial_restore_value (string): value of the `name` tag to be restored. This is the
                result of the revert of versions before oldest_version.

        Returns:
            osmium.OSMObject: a instance of one of the subclasses of osmium.OSMObject or None

            ``None`` will be returned if no changes are necessary to the latest version.
        """
        v = oldest_version.version + 1
        v_max = latest_version.version
        this_version = oldest_version
        conflict_solution = False
        osm_type = obj_to_str(oldest_version)
        bad_changesets = set()
        changes = {}
        while v <= v_max:
            # get next version
            if v < v_max:
                response, next_version = self.api_client.get_version(osm_type, oldest_version.id, v, False)
            else:
                response = OsmApiResponse.EXISTS
                next_version = latest_version
            if response == OsmApiResponse.REDACTED:
                # the queried version is redacted, skip it
                v += 1
                continue
            if v in bad_versions and self.is_malicious_change(this_version, next_version):
                self.do_changes(this_version, next_version, changes)
                bad_changesets.add(next_version.changeset)
                conflict_solution = True
            self.apply_good_changes(this_version, next_version, changes)
            this_version = next_version
            v += 1
        if conflict_solution:
            sys.stderr.write("Solved conflict on tags of {} {}\n".format(obj_to_str(this_version), this_version.id))
        if len(changes) == 0:
            return None, None
        new_version = latest_version
        edited = False
        # applying changes
        for k, v in changes.items():
            if new_version.tags.get(k, "") == "" or new_version.tags[k] != v:
                new_version.tags[k] = v
                edited = True
        if not edited:
            return None, None
        return new_version, bad_changesets

    def handle_multiple_versions(self, objects):
        bad_versions = [x.version for x in objects]
        osm_type = obj_to_str(objects[0])
        response, latest_version = self.api_client.get_latest_version(osm_type, objects[0].id)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            return None, None
        if objects[0].version == 1:
            sys.stdout.write("manual action necessary for {} {} {}\n".format(obj_to_str(objects[0]), objects[0].id, objects[0].version))
            return None, None
        response, prev_version = self.api_client.get_version(osm_type, objects[0].id, objects[0].version - 1)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            return None, None
        return self.solve_conflict(prev_version, latest_version, bad_versions)
