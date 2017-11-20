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
            sys.stderr.write("Failed to read password, quitting.\n")
            exit(1)
