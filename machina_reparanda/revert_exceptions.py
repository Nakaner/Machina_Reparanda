"""
© 2018 Michael Reichert

This file is part of Machina Reparanda.

osmi_simple_views is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

osmi_simple_views is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with osmi_simple_views. If not, see <http://www.gnu.org/licenses/>.
"""

class OSMException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Unknown error"
        super(OSMException, self).__init__(msg)


class TagInvalidException(OSMException):
    def __init__(self, tag, msg=None):
        super(TagInvalidException, self).__init__(msg)
        self.tag = tag


class ProgrammingError(RuntimeError):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Unknown programming error"
        super(OSMException, self).__init__(msg)
