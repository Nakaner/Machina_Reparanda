import requests
import sys

api_url = "https://api.openstreetmap.org/api/0.6/"
date_format = "%Y-%m-%dT%H:%M:%S"
user_agent = "machina_reparanda"


def download_changeset(changeset_id):
    """Download a changeset DIFF file from the OSM API.
    """
    url = "{}changeset/{}/download".format(api_url, changeset_id)
    sys.stderr.write("fetching OSC file from {} ...".format(url))
    header = {"user-agent": user_agent}
    r = requests.get("{}changeset/{}/download".format(api_url, changeset_id), timeout=300, stream=True, headers=header)
    sys.stderr.write(" {}\n".format(r.status_code))
    r.raise_for_status()
    return r.content
