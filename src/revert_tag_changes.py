#! /usr/bin/env python3

import sys
import argparse
import json
from sort_functions import type_to_int
from worker import Worker
from input_handler import InputHandler
from configuration import Configuration

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="path to configuration file if not located at ~/.machina_reparanda", default="~/.machina_reparanda")
parser.add_argument("bad_uid", help="ID of the user whose edits are reverted")
parser.add_argument("comment", help="changeset comment")
parser.add_argument("osc_files", help="OSC files", nargs="+")
args = parser.parse_args()

input_files = args.osc_files

# read configuration
with open(args.config, "r") as config_file:
    config_dict = json.load(config_file)
    configuration = Configuration(config_dict)

configuration.comment = args.comment
configuration.bad_uid = int(args.bad_uid[0])

objects = []
input_handler = InputHandler(objects)
for filename in input_files:
    sys.stderr.write("Reading {}\n".format(filename))
    input_handler.apply_file(filename)

# sort by object type, ID and version
sys.stderr.write("Sorting objects\n")
sorted(objects, key=lambda obj: (type_to_int(obj), obj.id, obj.version))

# Now the main task begins.
worker = Worker(objects, configuration)
worker.work()
