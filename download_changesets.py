#! /usr/bin/env python3

"""
© 2026 Michael Reichert

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
import os.path
import argparse
import requests
import urllib.parse
from machina_reparanda.utils import download_changeset


def split_row(row):
    ids = []
    splitted_by_space = row.strip().split(" ")
    for elem in splitted_by_space:
        splitted_by_comma = elem.split(",")
        for el in splitted_by_comma:
            parsed_id = int(el)
            ids.append(parsed_id)
    return ids


def download_and_write(changeset_id, path):
    try:
        changeset_data = download_changeset(changeset_id)
    except requests.exceptions.HTTPError as err:
        sys.stderr.write("Failed to fetch the contents of changeset {}: {}\n".format(cs_id, r.raise_for_status()))
        exit(1)
    except requests.exceptions.Timeout as err:
        sys.stderr.write("Failed to fetch the contents of changeset {}: {}\n".format(cs_id, err))
    try:
        with open(dest_file_path, "wb") as oscfile:
            oscfile.write(changeset_data)
    except Exception as err:
        sys.stderr.write("Failed to write OSC file: {}\n".format(err))
        exit(1)


parser = argparse.ArgumentParser(description="Download a list of changesets from the API. Reads list separated by space, comma or newline from standard input.")
parser.add_argument("-o", "--osc-output-dir", help="output directory for downloaded content of the changesets (OSC format)", type=str, default=None)
args = parser.parse_args()

for row in sys.stdin:
    current_ids = split_row(row)
    for cs_id in current_ids:
        file_name = "c{}.osc".format(cs_id)
        dest_file_path = os.path.join(args.osc_output_dir, file_name)
        download_and_write(cs_id, dest_file_path)
        #sys.stderr.write("{}\n".format(cs_id))
