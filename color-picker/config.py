import os
import json

configuration = {}

try:
  if os.environ["ENVIRONMENT"] == "production":
    configuration = {
			"guild_id": int(os.environ["GUILD_ID"]),
			"connection_string": os.environ["CONNECTION_STRING"],
			"token": os.environ["TOKEN"]
    }
except KeyError:
	with open("config.json", "r") as file:
		configuration = json.load(file)

import psycopg2_pool

pool = psycopg2_pool.ConnectionPool(minconn=5, maxconn=20, dsn=configuration["connection_string"], idle_timeout=60)

def select_one(query, params):
	with pool.getconn() as conn:
		with conn.cursor() as cursor:
			cursor.execute(query, params)
			result = cursor.fetchone()
	
	return result

from colorthief import ColorThief
import aiohttp
from io import BytesIO

async def get_buffer_from_url(url):
	buffer: BytesIO
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as response:
			if response.status == 200:
				buffer = BytesIO(await response.read())
	
	return buffer

async def get_dominant_colors(member_avatar_url):
	buffer = await get_buffer_from_url(member_avatar_url)
	color_palette = ColorThief(buffer).get_palette()

	dominant_colors = [rgb_to_hex(color) for color in color_palette]
	
	return dominant_colors

def rgb_to_hex(rgb):
	return "%02x%02x%02x" % (rgb)