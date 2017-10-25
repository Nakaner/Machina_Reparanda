from sort_functions import equal_type_id
from revert_implementation import RevertImplementation
from update_writer import OsmApiUploader


class Worker():
    def __init__(self, objects, configuration):
        self.objects = objects
        self.configuration = configuration
        self.uploader = OsmApiUploader(self.configuration)
        self.revert_impl = RevertImplementation(self.configuration)

    def work(self):
        current_idx = 0
        next_idx = 1
        while current_idx < len(self.objects):
            if next_idx >= len(self.objects):
                new_object = self.revert_impl.decide_and_do(self.objects[current_idx:next_idx])
                self.uploader.handle_object(new_object)
                break
            if equal_type_id(self.objects[current_idx], self.objects[next_idx]):
                next_idx = next_idx + 1
                continue
            else:
                new_object = self.revert_impl.decide_and_do(self.objects[current_idx:next_idx])
                current_idx = next_idx
                next_idx = next_idx + 1
                self.uploader.handle_object(new_object)
        self.uploader.close_changeset()
