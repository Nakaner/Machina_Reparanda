#! /usr/bin/env python3

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

import sys
import re
import datetime
import argparse
import osmium
import requests
import urllib.parse

API_URL = "https://api.openstreetmap.org/api/0.6/"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class CSHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.last_timestamp = datetime.datetime.utcnow()
        self.count = 0

    def reset(self):
        self.count = 0

    def changeset(self, cs):
        self.last_timestamp = cs.created_at
        for key in keys_to_search:
            comment = cs.tags.get(key, "")
            result = re.search(pattern, comment)
            if (not args.invert and result is not None) or (args.invert and result is None):
                sys.stdout.write("{}\n".format(cs.id))
                break


class CSDownloader():
    def __init__(self, user, uid, since, to, handler):
        if user is not None and uid is not None:
            raise Exception("You must not specify both the user name and the UID")
        if user is None and uid is None:
            raise Exception("You must specify either the user name or the UID")
        self.user = user
        self.uid = uid
        self.since = datetime.datetime.strptime(since, DATE_FORMAT)
        self.handler = handler
        self.date_to = datetime.datetime.strptime(to, DATE_FORMAT)

    def _query_string(self):
        params = []
        if self.user:
            params.append("display_name={}".format(urllib.parse.quote(self.user)))
        if self.uid:
            params.append("uid={}".format(self.uid))
        params.append("time={},{}".format(self.since.strftime(DATE_FORMAT), self.date_to.strftime(DATE_FORMAT)))
        return "&".join(params)

    def next(self):
        self.handler.reset()
        sys.stderr.write("downloading changeset list, changesets before {}\n".format(self.since.strftime(DATE_FORMAT)))
        url = "{}changesets?{}".format(API_URL, self._query_string())
        r = requests.get(url)
        if r.status_code == 200:
            self.handler.apply_buffer(r.content, "osm")
            self.date_to = self.handler.last_timestamp
        return self.handler.count > 0


parser = argparse.ArgumentParser(description="Search in changeset metadata files")
parser.add_argument("-v", "--invert", help="invert match", action="store_true", default=False)
parser.add_argument("-r", "--regex", help="filter comment by regex", required=True)
parser.add_argument("-k", "--keys", help="comma separated list of changeset tag keys to compare with the regular expression", default="comment")
parser.add_argument("-i", "--ignore-case", help="don't filter case sensitive", action="store_true", default=False)
parser.add_argument("-d", "--download", help="download the list of changesets from the OSM API", action="store_true", default=False)
parser.add_argument("--download-user", help="name of the user whose changesets should be downloaded")
parser.add_argument("--download-uid", help="UID of the user whose changesets should be downloaded", type=int)
parser.add_argument("--download-since", help="oldest timestamp for changesets to be downloaded, format: YYYY-mm-ddTHH:MM:SS")
parser.add_argument("--download-to", help="newest timestamp for changesets to be downloaded, format: YYYY-mm-ddTHH:MM:SS", default=datetime.datetime.utcnow().strftime(DATE_FORMAT))
parser.add_argument("-f", "--input-file", help="XML file containing changeset metadata", type=str, default=None)
args = parser.parse_args()

flags = re.IGNORECASE if args.ignore_case else 0
pattern = re.compile(args.regex, flags)

keys_to_search = args.keys.split(",")

h = CSHandler()
if args.download:
    downloader = CSDownloader(args.download_user, args.download_uid, args.download_since, args.download_to, h)
    while True:
        if not downloader.next():
            break
elif args.input_file:
    h.apply_file(args.input_file)
else:
    sys.stderr.write("ERROR: no input given\n")
    exit(1)
