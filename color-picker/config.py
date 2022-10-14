import os
import json

configuration = {}
with open("config.json", "r") as file:
  configuration = json.load(file)

try:
  if os.environ["ENVIRONMENT"] == "production":
    configuration = {
			"guild_id": int(os.environ["GUILD_ID"]),
			"database_name": os.environ["DATABASE_NAME"],
			"database_user": os.environ["DATABASE_USER"],
			"database_password": os.environ["DATABASE_PASSWORD"],
			"database_host": os.environ["DATABASE_HOST"],
			"database_port": os.environ["DATABASE_PORT"],
			"token": os.environ["TOKEN"]
    }
except KeyError:
  pass