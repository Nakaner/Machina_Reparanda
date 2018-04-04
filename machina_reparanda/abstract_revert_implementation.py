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

from .sort_functions import obj_to_str
from .osm_api_functions import OsmApiResponse, OsmApiClient


class AbstractRevertImplementation:
    """
    Base class for all revert implementation

    This class defines a callback which decides which callback of an implementation should be
    called for a revert of an object.
    """

    def __init__(self, configuration, api_client):
        self.configuration = configuration
        self.api_client = api_client

    def decide_and_do(self, objects):
        if len(objects) == 1:
            return self.work_on_single_object(objects[0])
        elif len(objects) > 1:
            return self.handle_multiple_versions(objects)

    def work_on_single_object(self, obj):
        if obj.version == 1:
            return self.handle_v1_object(obj)
        return self.handle_obj(obj)
