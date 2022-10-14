import os
import json

configuration = {}
with open("config.json", "r") as file:
  configuration = json.load(file)

try:
  if os.environ["ENVIRONMENT"] == "production":
    configuration = {
      "guild_id": os.environ["GUILD_ID"],
      "token": os.environ["TOKEN"],
    }
except KeyError:
  pass