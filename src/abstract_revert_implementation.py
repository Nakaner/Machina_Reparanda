from .sort_functions import obj_to_str
from .osm_api_functions import OsmApiResponse, OsmApiClient


class AbstractRevertImplementation:
    def __init__(self, configuration, api_client):
        self.configuration = configuration
        self.api_client = api_client
