import io
import os
import re
import json
from datetime import timedelta

import wonderwords
from PIL import Image, ImageDraw, ImageFont

import logging

configuration = {}

from discord import Color
COLORS = {
	"teal": Color.teal(),
	"dark_teal": Color.dark_teal(),
	"brand green": Color.brand_green(),
	"green": Color.green(),
	"dark_green": Color.dark_green(),
	"blue": Color.blue(),
	"dark_blue": Color.dark_blue(),
	"magenta": Color.magenta(),
	"dark magenta": Color.dark_magenta(),
	"gold": Color.gold(),
	"dark gold": Color.dark_gold(),
	"orange": Color.orange(),
	"dark orange": Color.dark_orange(),
	"brand red": Color.brand_red(),
	"red": Color.red(),
	"dark red": Color.dark_red(),
	"lighter grey": Color.lighter_grey(),
	"lighter gray": Color.lighter_gray(),
	"light grey": Color.light_grey(),
	"light gray": Color.light_gray(),
	"dark grey": Color.dark_grey(),
	"dark gray": Color.dark_gray(),
	"darker grey": Color.darker_grey(),
	"darker gray": Color.darker_gray(),
	"og blurple": Color.og_blurple(),
	"blurple": Color.blurple(),
	"greyple": Color.greyple(),
	"dark theme": Color.dark_theme(),
	"fuchsia": Color.fuchsia(),
	"yellow": Color.yellow(),
	"light_embed": Color.light_embed(),
	"dark embed": Color.dark_embed(),
}

try:
	configuration = {
    "owner_id": int(os.environ["OWNER_ID"]),
		"custom_role_id": int(os.environ["CUSTOM_ROLE_ID"]),
		"guild_id": int(os.environ["GUILD_ID"]),
		"role_ids": [int(role_id) for role_id in os.environ["ROLE_IDS"].split(",")],
		"emoji_server_id": int(os.environ["EMOJI_SERVER_ID"]),
		"connection_string": os.environ["CONNECTION_STRING"],
		"token": os.environ["TOKEN"]
	}
except KeyError:
	configuration = json.loads(
		open("config.json", 'r').read()
	)

import psycopg2_pool

pool = psycopg2_pool.ConnectionPool(minconn=5, maxconn=20, dsn=configuration["connection_string"], idle_timeout=60)

def execute_query(query, params=None):
  with pool.getconn() as conn:
    with conn.cursor() as cursor:
      if params:
        cursor.execute(query, params)
      else:
        cursor.execute(query)
      conn.commit()

def delete_query(query):
  execute_query(query)

def insert_query(query):
  execute_query(query)

def insert_with_params(query, params):
  execute_query(query, params)

def select_one(query):
  with pool.getconn() as conn:
    with conn.cursor() as cursor:
      cursor.execute(query)
      result = cursor.fetchone()
		
  return result

def select_all(query):
  with pool.getconn() as conn:
    with conn.cursor() as cursor:
      cursor.execute(query)
      result = cursor.fetchall()
		
  return result

def get_maaldar_user(user_id):
  return select_one(f"SELECT * FROM Maaldar WHERE user_id = '{user_id}'")

DAYS_IN_SECONDS_REQUIRED_FOR_ROLE = 15_552_000

def is_old_maaldar(user_id):
	data = select_one(f"SELECT boosting_since FROM MaaldarDuration WHERE user_id = '{user_id}'")
	if data is None:
		return False
  
	return data[0] >= DAYS_IN_SECONDS_REQUIRED_FOR_ROLE

def make_image(dominant_color):
	image = Image.new(
		mode="RGBA", 
		size=(50, 50),
		color=(0, 0, 0, 0)
	)
	ImageDraw.Draw(image).rounded_rectangle(
		(0, 0, 50, 50), 
		radius=20,
		fill=dominant_color
	)
	return image

def concatenate_images(images):
	# size = width of 10 images and height of 1 image
	image = Image.new(
		mode="RGBA", 
		size=(50 * 10, 50),
		color=(0, 0, 0, 0)
	)
	ImageDraw.Draw(image).rounded_rectangle(
		(0, 0, 500, 50), 
		radius=20
	)

	width = 0
	for index, image_to_paste in enumerate(images, start=1):
		font = ImageFont.load_default()
		font
		draw = ImageDraw.Draw(image_to_paste)
		draw.text(
			(10, 10), 
			f"{index}", 
			font=font,
			stroke_width=1, 
			stroke_fill="white"
		)

		image.paste(image_to_paste, (width, 0))
		width += 50

	bytes_array = io.BytesIO()
	image.save(bytes_array, format="PNG")
	bytes_array.seek(0)

	return bytes_array

def rgb_to_hex(rgb):
	return "%02x%02x%02x" % (rgb)

def match_url_regex(string):
	# It works 🤷‍♀️
	return re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', string, re.IGNORECASE)

def create_session_token() -> str:
	random_word = wonderwords.RandomWord()
	session_tokens: list[str] = random_word.random_words(5, word_max_length=4, include_parts_of_speech=["verbs", "nouns"])
	session_tokens = [token.capitalize() for token in session_tokens]
	session = "".join(session_tokens)
	
	return session
