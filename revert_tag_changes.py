#! /usr/bin/env python3

import sys
import argparse
import json
import logging
from machina_reparanda.sort_functions import type_to_int
from machina_reparanda.worker import Worker
from machina_reparanda.input_handler import InputHandler
from machina_reparanda.configuration import Configuration

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--automatic-conflict-solution", help="add conflicts_automatically_resolved=yes to all uploaded changesets", action="store_true", default=False)
parser.add_argument("-c", "--config", help="path to configuration file if not located at ~/.machina_reparanda", default="~/.machina_reparanda")
parser.add_argument("-d", "--dryrun", help="dryrun mode (no uploads)", action="store_true", default=False)
parser.add_argument("-i", "--implementation", help="path to Python file where a class RevertImplementation is provided which implements the revert", default=None)
parser.add_argument("-l", "--log-level", help="log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", default="INFO", type=str)
parser.add_argument("-S", "--no-comment-reverted", help="don't post a changeset comment to all reverted changesets (e.g. to avoid email spamming)", action="store_true", default=False)
parser.add_argument("-r", "--reuse-changeset", help="reuse changeset with the given ID", type=int, default=0)
parser.add_argument("comment", help="changeset comment")
parser.add_argument("osc_files", help="OSC files", nargs="+")
args = parser.parse_args()

# log level
numeric_log_level = getattr(logging, args.log_level.upper())
if not isinstance(numeric_log_level, int):
    raise ValueError("Invalid log level {}".format(args.log_level.upper()))
logging.basicConfig(level=numeric_log_level)

# reduce log level for requests and urllib3
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

input_files = args.osc_files

# read configuration
with open(args.config, "r") as config_file:
    config_dict = json.load(config_file)
    configuration = Configuration(config_dict)

configuration.automatic_conflict_solution = args.automatic_conflict_solution
configuration.dryrun = args.dryrun
configuration.comment_reverted = not args.no_comment_reverted
configuration.comment = args.comment
configuration.reuse_changeset = args.reuse_changeset
if not hasattr(configuration, "implementation") and args.implementation is None:
    sys.stderr.write("ERROR: No implementation was provided to be used for this revert.\n")
    sys.stderr.write("Please either provide a path in the configration file or use -i.\n")
    parser.print_help()
    exit(1)
elif args.implementation is not None:
    configuration.implementation = args.implementation

objects = []
input_handler = InputHandler(objects)
logging.info("Reading input files ...")
for filename in input_files:
    logging.debug("Reading {}".format(filename))
    input_handler.apply_file(filename)

# sort by object type, ID and version
logging.info("Sorting objects ...")
objects.sort(key=lambda obj: (type_to_int(obj), obj.id, obj.version))

# Now the main task begins.
worker = Worker(objects, configuration)
worker.work()
