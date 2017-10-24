import sys
import re
from sort_functions import obj_to_str
from osm_api_functions import *

def handle_v1_object(obj):
    pattern = "[A-Za-z] \(.+\)$"
    if "name" in obj.tags and re.search(pattern, obj.tags["name"]) != None:
        sys.stdout.write("manual action necessary for {} {}\n".format(obj_to_str(obj), obj.version))

def is_malicious_change(prev_version, this_version):
    if "name" not in prev_version.tags or "name" not in this_version.tags:
        # if one version does not contain a name tag, ignore the change
        return False
    if prev_version.tags["name"] == this_version.tags["name"]:
        # no change by user → no action necessary
        return False
    if "highway" in prev_version.tags and "highway" in this_version.tags:
        return True

def handle_obj(obj):
    # get previous version
    api_client = OsmApiClient(obj)
    api_client.get_version(obj.version - 1)
    if api_client.status == OsmApiResponse.REDACTED:
        handle_v1_object(obj)
        return None
    prev_version = api_client.retrieved_object
    if not is_malicious_change(prev_version, obj):
        return None
    # fetch latest version
    api_client_latest = OsmApiClient(obj)
    api_client_latest.get_latest_version()
    if api_client_latest.status == OsmApiResponse.DELETED:
        # object is deleted, nothing to do
        return None
    if api_client_latest.status == OsmApiResponse.NOT_FOUND:
        sys.stderr.write("API returned 404 for {}\n".format(api_client_latest.url))
        return None
    if api_client_latest.status == OsmApiResponse.ERROR:
        sys.stderr.write("API returned an error code for {}\n".format(api_client_latest.url))
    latest_version = api_client_latest.retrieved_object
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

def decide_and_do(objects):
    if len(objects) == 1:
        return work_on_single_object(objects[0])
    elif len(objects) > 1:
        # handle multi version objects
        #TODO work on all versions
        return work_on_single_object(objects[0])

def work_on_single_object(obj):
    if obj.version == 1:
        handle_v1_object(obj)
        return None
    return handle_obj(obj)

