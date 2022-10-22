import io
import os
import re
import sys
import json

from PIL import Image, ImageDraw, ImageFont

configuration = {}
try:
	configuration = json.loads(
		open("config.json", 'r').read()
	)
except:
	if os.environ["ENVIRONMENT"] == "PRODUCTION":
		configuration = {
			"custom_role_id": int(os.environ["CUSTOM_ROLE_ID"]),
			"guild_id": int(os.environ["GUILD_ID"]),
			"role_ids": [int(role_id) for role_id in os.environ["ROLE_IDS"].split(",")],
			"emoji_server_id": int(os.environ["EMOJI_SERVER_ID"]),
			"database_name": os.environ["DATABASE_NAME"],
			"database_user": os.environ["DATABASE_USER"],
			"database_password": os.environ["DATABASE_PASSWORD"],
			"database_host": os.environ["DATABASE_HOST"],
			"database_port": int(os.environ["DATABASE_PORT"]),
			"token": os.environ["TOKEN"]
		}

def get_maaldar_user(user_id):
	cursor = configuration["database"].cursor
	cursor.execute(
			f"SELECT * FROM Maaldar WHERE user_id = '{user_id}'"
	)
	return cursor.fetchone()

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
	return re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', string)
