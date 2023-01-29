import os
import json

configuration = {}
with open("config.json", "r") as file:
  configuration = json.load(file)

try:
  if os.environ["ENVIRONMENT"] == "production":
    configuration = {
			"guild_id": int(os.environ["GUILD_ID"]),
			"connection_string": os.environ["CONNECTION_STRING"],
			"token": os.environ["TOKEN"]
    }
except KeyError:
  pass

import psycopg2_pool

pool = psycopg2_pool.ConnectionPool(minconn=5, maxconn=20, dsn=configuration["connection_string"], idle_timeout=60)

def select_one(query, params):
	with pool.getconn() as conn:
		with conn.cursor() as cursor:
			cursor.execute(query, params)
			result = cursor.fetchone()
	
	return result