import sys
import re
from abstract_revert_implementation import AbstractRevertImplementation, obj_to_str, OsmApiResponse, OsmApiClient


class RevertImplementation(AbstractRevertImplementation):
    def __init__(self, configuration):
        super().__init__(configuration)

    def handle_v1_object(self, obj):
        pattern = "[A-Za-z] \(.+\)$"
        if "name" in obj.tags and re.search(pattern, obj.tags["name"]) is not None:
            sys.stdout.write("manual action necessary for {} {}\n".format(obj_to_str(obj), obj.version))

    def is_malicious_change(self, prev_version, this_version):
        if "name" not in prev_version.tags or "name" not in this_version.tags:
            # if one version does not contain a name tag, ignore the change
            return False
        if prev_version.tags["name"] == this_version.tags["name"]:
            # no change by user → no action necessary
            return False
        if "highway" in prev_version.tags and "highway" in this_version.tags:
            return True

    def handle_obj(self, obj):
        # get previous version
        api_client = OsmApiClient(self.configuration)
        response, prev_version = api_client.get_version(obj, obj.version - 1)
        if response == OsmApiResponse.REDACTED:
            # all previous versions are redacted
            self.handle_v1_object(obj)
            return None
        if not self.is_malicious_change(prev_version, obj):
            return None
        # fetch latest version
        response, latest_version = api_client.get_latest_version(obj)
        if response in [OsmApiResponse.DELETED, OsmApiResponse.NOT_FOUND, OsmApiResponse.ERROR]:
            return None
        # check if this is the latest version
        if "name" not in latest_version.tags:
            # name tag has been deleted in the meanwhile, no action necessary
            return None
        if obj.tags["name"] == latest_version.tags["name"]:
            # conflict on this tag, revert easy
            sys.stderr.write("ACTION: modify name tag of {} {} from \"{}\" to \"{}\"\n".format(obj_to_str(obj), obj.id, latest_version.tags["name"], prev_version.tags["name"]))
            new_version = latest_version
            new_version.tags["name"] = prev_version.tags["name"]
            #new_version.version += 1
            return new_version
        else:
            # modification in the meanwhile, conflict on this tag, revert difficult
            sys.stderr.write("CONFLICT: {} {}, server version: {}, my version: {}\n".format(obj_to_str(obj), obj.id, latest_version.version, obj.version))
        return None

    def handle_multiple_verisons(self, obj):
        pass

    def decide_and_do(self, objects):
        if len(objects) == 1:
            return self.work_on_single_object(objects[0])
        elif len(objects) > 1:
            # handle multi version objects
            # TODO work on all versions
            return self.work_on_single_object(objects[0])

    def work_on_single_object(self, obj):
        if obj.version == 1:
            self.handle_v1_object(obj)
            return None
        return self.handle_obj(obj)
