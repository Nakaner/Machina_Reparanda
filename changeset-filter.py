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
import argparse
import osmium

class CSHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)

    def changeset(self, cs):
        for key in keys_to_search:
            comment = cs.tags.get(key, "")
            result = re.search(pattern, comment)
            if (not args.invert and result is not None) or (args.invert and result is None):
                sys.stdout.write("{}\n".format(cs.id))
                break

parser = argparse.ArgumentParser(description="Search in changeset metadata files")
parser.add_argument("-v", "--invert", help="invert match", action="store_true", default=False)
parser.add_argument("-r", "--regex", help="filter comment by regex", required=True)
parser.add_argument("-k", "--keys", help="comma separated list of changeset tag keys to compare with the regular expression", default="comment")
parser.add_argument("-i", "--ignore-case", help="don't filter case sensitive", action="store_true", default=False)
parser.add_argument("changeset_list", help="XML file containing changeset metadata")
args = parser.parse_args()

flags = re.IGNORECASE if args.ignore_case else 0
pattern = re.compile(args.regex, flags)

keys_to_search = args.keys.split(",")

h = CSHandler()
h.apply_file(args.changeset_list)
