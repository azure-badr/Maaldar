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

import psycopg2
database_name = configuration["database_name"]
database_user = configuration["database_user"]
database_password = configuration["database_password"]
database_host = configuration["database_host"]
database_port = configuration["database_port"]

connection_string = f"dbname={database_name} user={database_user} password={database_password} host={database_host} port={database_port}"

def select_one(query, params):
	with psycopg2.connect(connection_string) as connection:
		with connection.cursor() as cursor:
			cursor.execute(query, params)
			return cursor.fetchone()