#! /usr/bin/env python3

import sys
import argparse
import json
from machina_reparanda.sort_functions import type_to_int
from machina_reparanda.worker import Worker
from machina_reparanda.input_handler import InputHandler
from machina_reparanda.configuration import Configuration

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="path to configuration file if not located at ~/.machina_reparanda", default="~/.machina_reparanda")
parser.add_argument("-i", "--implementation", help="path to Python file where a class RevertImplementation is provided which implements the revert", default=None)
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
if not hasattr(configuration, "implementation") and args.implementation is None:
    sys.stderr.write("ERROR: No implementation was provided to be used for this revert.\n")
    sys.stderr.write("Please either provide a path in the configration file or use -i.\n")
    parser.print_help()
    exit(1)
elif args.implementation is not None:
    configuration.implementation = args.implementation

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
