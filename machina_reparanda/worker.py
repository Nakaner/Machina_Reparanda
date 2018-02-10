import os
import sys
import importlib.util
#import importlib.machinery

from .sort_functions import equal_type_id
from .update_writer import OsmApiUploader
from .osm_api_functions import OsmApiClient


class Worker():
    def __init__(self, objects, configuration):
        self.objects = objects
        self.configuration = configuration
        self.uploader = OsmApiUploader(self.configuration)
        self.api_client = OsmApiClient(self.configuration)
        abspath = os.path.abspath(self.configuration.implementation)
        path, name = os.path.split(abspath)
        module_name, ext = os.path.splitext(name)
        #module_name, ext = "{}.{}".format("implementations", os.path.splitext(name))
        sys.stderr.write("module_name: {}\n".format(module_name))
        try:
            #module = importlib.machinery.SourceFileLoader(module_name, self.configuration.implementation).exec_module()
            spec = importlib.util.spec_from_file_location(module_name, abspath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[module_name] = module
            self.revert_impl = module.RevertImplementation(self.configuration, self.api_client)
        except ImportError as err:
            sys.stderr.write("Error while loading revert implementation from {}: {}\n".format(abspath, err))
            exit(1)

    def comment_reverted_changesets(self, changesets):
        text = "This changeset has been reverted fully or in part by one or multiple of the following changesets: "
        ids = ", ".join(str(cs_id) for cs_id in self.uploader.used_changesets)
        text += ids
        text += "\n\nThe reason for the revert is: {}".format(self.configuration.comment)
        for cs_id in changesets:
            self.uploader.comment_changeset(cs_id, text)

    def work(self):
        current_idx = 0
        next_idx = 1
        reverted_changesets = set()
        while current_idx < len(self.objects):
            if next_idx >= len(self.objects):
                new_object, changesets = self.revert_impl.decide_and_do(self.objects[current_idx:next_idx])
                if new_object is not None and changesets is not None:
                    self.uploader.handle_object(new_object, changesets)
                    reverted_changesets = reverted_changesets | changesets
                break
            if equal_type_id(self.objects[current_idx], self.objects[next_idx]):
                next_idx = next_idx + 1
                continue
            else:
                new_object, changesets = self.revert_impl.decide_and_do(self.objects[current_idx:next_idx])
                current_idx = next_idx
                next_idx = next_idx + 1
                if new_object is not None and changesets is not None:
                    self.uploader.handle_object(new_object, changesets)
                    reverted_changesets = reverted_changesets | changesets
        self.uploader.close_changeset()
        if self.config.comment_reverted:
            self.comment_reverted_changesets(reverted_changesets)
