import sys


class Configuration:
    def __init__(self, config):
        try:
            self.user = config["user"]
            self.uid = config["uid"]
        except KeyError as e:
            sys.stderr.write(e)
            exit(1)
        self.user_agent = config.get("user_agent", "machina_reparanda")

        self.api_url = "https://master.apis.dev.openstreetmap.org/api/0.6"
        if "api_url" in config:
            self.api_url = config["api_url"]
        if "password" in config:
            self.password = config["password"]
        else:
            self.password_promt()

    def password_promt(self):
        password = input("Enter your OSM password:\n")
        if password != "":
            self.password = password
        else:
            sys.stderr.write("Failed to read password, quitting.\n")
            exit(1)
