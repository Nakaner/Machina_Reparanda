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

import logging

class Configuration:
    """
    Configuration of the library/revert program
    """

    def __init__(self, config):
        try:
            self.user = config["user"]
            self.uid = config["uid"]
        except KeyError as e:
            logging.critical(e)
            exit(1)
        self.user_agent = config.get("user_agent", "machina_reparanda")

        self.api_url = config.get("api_url", "https://master.apis.dev.openstreetmap.org/api/0.6")
        if "password" in config:
            self.password = config["password"]
        else:
            self.password = self.password_prompt()

    def password_prompt(self):
        password = input("Enter your OSM password:\n")
        if password != "":
            return password
        else:
            logging.critical("Failed to read password, quitting.")
            exit(1)
