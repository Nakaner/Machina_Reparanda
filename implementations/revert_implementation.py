import sys
import re
from machina_reparanda.abstract_revert_implementation import AbstractRevertImplementation
from machina_reparanda.sort_functions import obj_to_str
from machina_reparanda.osm_api_functions import OsmApiResponse


def get_next_greater_or_equal_element(the_list, current_value):
    for i in range(0, len(the_list)):
        if the_list[i] >= current_value:
            return i
    return len(the_list)


class RevertImplementation(AbstractRevertImplementation):
    def __init__(self, configuration, api_client):
        super().__init__(configuration, api_client)

    def handle_v1_object(self, obj):
        if "name" in obj.tags and self.name_has_bad_format(obj.tags.get("name", "")):
            sys.stdout.write("manual action necessary for {} {}\n".format(obj_to_str(obj), obj.version))
        return None, None

    def name_has_bad_format(self, name_tag):
        pattern = "[A-Za-z] \(.+\)$"
        return re.search(pattern, name_tag) is not None

    def is_malicious_change(self, prev_version, this_version):
        if "name" not in prev_version.tags or "name" not in this_version.tags:
            # if one version does not contain a name tag, ignore the change
            return False
        if prev_version.tags.get("name", "") == this_version.tags.get("name", ""):
            # no change by user → no action necessary
            return False
        if "highway" in prev_version.tags and "highway" in this_version.tags:
            return True
        return False

    def handle_obj(self, obj):
        # get latest version
        obj_type = obj_to_str(obj)
        response, latest_version = self.api_client.get_latest_version(obj_type, obj.id)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            return None, None
        # check if this is the latest version
        if "name" not in latest_version.tags:
            # name tag has been deleted in the meanwhile, no action necessary
            return None, None
        # get previous version
        response, prev_version = self.api_client.get_version(obj_type, obj.id, obj.version - 1)
        if response == OsmApiResponse.REDACTED:
            # all previous versions are redacted
            return self.handle_v1_object(obj)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            return None, None
        name_changed, new_value =  self.has_tag_changed(prev_version, obj, "name")
        if self.is_interesting_object(prev_version) and self.is_interesting_object(obj) and name_changed:
            if latest_version.version > obj.version:
                # conflict
                sys.stderr.write("CONFLICT (will be solved automatically): {} {}, could provide version {}, got version {} from API\n".format(obj_to_str(obj), obj.id, obj.version, latest_version.version))
                return self.solve_conflict(prev_version, latest_version, [obj.version])
            sys.stderr.write("ACTION: modify name tag of {} {} from \"{}\" to \"{}\"\n".format(obj_to_str(obj), obj.id, latest_version.tags.get("name", ""), prev_version.tags.get("name", "")))
            new_version = obj
            new_value = prev_version.tags.get("name", "")
            if new_value == "":
                new_version.tags.pop("name", None)
            else:
                new_version.tags["name"] = new_value
            return new_version, {obj.changeset}
        sys.stderr.write("{} {} {} is not interesting or nothing has to be done\n".format(obj_to_str(obj), obj.id, obj.version))
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

    def is_interesting_object(self, osm_object):
        return "highway" in osm_object.tags

    def solve_conflict(self, oldest_version, latest_version, bad_versions, **kwargs):
        """
        Check if all versions of an object from from_version to the latest version
        contain only "good" changes.

        Args:
            oldest_version (osmium.mutable.osm.OSMObject): oldest version of the object to be scanned
            latest_version (osmium.mutable.osm.OSMObject): latest version of the object (usually retrieved from the API)
            bad_versions (list of int): list of version numbers which are considered bad

        Kwargs:
            initial_restore_value (string): value of the `name` tag to be restored. This is the
                result of the revert of versions before oldest_version.

        Returns:
            osmium.OSMObject: a instance of one of the subclasses of osmium.OSMObject or None

            ``None`` will be returned if no changes are necessary to the latest version.
        """
        #TODO check if the implementation differs from the multi-version method
        v = oldest_version.version + 1
        v_max = latest_version.version
        this_version = oldest_version
        to_restore = kwargs.get("initial_restore_value", oldest_version.tags.get("name", ""))
        #TODO the use of conflict_solution is questionable
        conflict_solution = False
        osm_type = obj_to_str(oldest_version)
        bad_changesets = set()
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
            changed, new_value = self.has_tag_changed(this_version, next_version, "name")
            if v not in bad_versions:
                if changed:
                    to_restore = new_value
                    conflict_solution = True
            elif v in bad_versions and self.is_interesting_object(this_version) and self.is_interesting_object(next_version):
                sys.stderr.write("Ignored change of name tag between version {} and {}\n".format(v-1, v))
                bad_changesets.add(next_version.changeset)
            elif v in bad_versions and changed:
                to_restore = new_value
                bad_changesets.add(next_version.changeset)
            this_version = next_version
            v += 1
        if conflict_solution:
            sys.stderr.write("Solved conflict on \"name\" tag of {} {}\n".format(obj_to_str(this_version), this_version.id))
        new_version = latest_version
        if to_restore == latest_version.tags.get("name", ""):
            # nothing to do
            return None, None
        if to_restore == "":
            new_version.tags.pop("name", None)
        else:
            new_version.tags["name"] = to_restore
        return new_version, bad_changesets

    def handle_multiple_versions(self, objects):
        bad_versions = [x.version for x in objects]
        osm_type = obj_to_str(objects[0])
        bad_changesets = set()
        response, latest_version = self.api_client.get_latest_version(osm_type, objects[0].id)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            return None, None
        if objects[0].version == 1:
            sys.stdout.write("manual action necessary for {} {} {}\n".format(obj_to_str(objects[0]), objects[0].id, objects[0].version))
            return None, None
        to_restore = ""
        for i in range(0, len(objects)):
            this_version = objects[i]
            if i == 0:
                response, prev_version = self.api_client.get_version(osm_type, this_version.id, this_version.version - 1)
                if response == OsmApiResponse.REDACTED:
                    # all previous versions are redacted
                    sys.stdout.write("manual action necessary for {} {} {}\n".format(obj_to_str(this_version), this_version.id, this_version.version))
                    return None, None
                to_restore = prev_version.tags.get("name", "")
            elif objects[i-1].version < this_version.version - 1:
                # There are version between this version and the previous version in the list. We
                # have to solve this conflict.
                response, prev_version = self.api_client.get_version(osm_type, this_version.id, objects[i-1].version - 1)
                return self.solve_conflict(objects[i-1], latest_version, bad_versions, prev_version, initial_restore_value=to_restore)
            else:
                response = OsmApiResponse.EXISTS
                prev_version = objects[i-1]
            if not self.is_interesting_object(prev_version) or not self.is_interesting_object(this_version):
                to_restore = this_version.tags.get("name", "")
            elif self.has_tag_changed(prev_version, this_version, "name"):
                bad_changesets.add(this_version.changeset)
        new_version = latest_version
        #TODO return None,None if no change necessary
        if to_restore == latest_version.tags.get("name", ""):
            # nothing to do
            return None, None
        if to_restore == "":
            new_version.tags.pop("name", None)
        else:
            new_version.tags["name"] = to_restore
        return new_version, bad_changesets

    def decide_and_do(self, objects):
        if len(objects) == 1:
            return self.work_on_single_object(objects[0])
        elif len(objects) > 1:
            return self.handle_multiple_versions(objects[0])

    def work_on_single_object(self, obj):
        if obj.version == 1:
            return self.handle_v1_object(obj)
        return self.handle_obj(obj)
