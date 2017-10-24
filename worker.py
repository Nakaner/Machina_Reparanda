from sort_functions import equal_type_id
from revert_implementation import decide_and_do
from update_writer import *
from configuration import *

class Worker():
    def __init__(self, objects, configuration):
        self.objects = objects
        self.configuration = configuration

    def work(self):
        current_idx = 0
        next_idx = 1
        uploader = OsmApiUploader(self.configuration)
        while current_idx < len(self.objects):
            if next_idx >= len(self.objects):
                new_object = decide_and_do(self.objects[current_idx:next_idx])
                uploader.handle_object(new_object)
                break
            if equal_type_id(self.objects[current_idx], self.objects[next_idx]):
                next_idx = next_idx + 1
                continue
            else:
                new_object = decide_and_do(self.objects[current_idx:next_idx])
                current_idx = next_idx
                next_idx = next_idx + 1
                uploader.handle_object(new_object)
        uploader.close_changeset()
            


