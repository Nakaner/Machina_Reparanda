from sort_functions import obj_to_str
from osm_api_functions import OsmApiResponse, OsmApiClient


class AbstractRevertImplementation:
    def __init__(self, configuration):
        self.configuration = configuration
