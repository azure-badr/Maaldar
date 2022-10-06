from PIL import Image, ImageDraw, ImageFont

import os
import re
import json
from sqlite3 import Cursor

import discord

configuration = json.loads(
	open("config.json", 'r').read()
)

if os.environ["ENVIRONMENT"] == "PRODUCTION":
	configuration = {
		"staff_channel_id": os.environ["STAFF_CHANNEL_ID"],
		"maaldar_role_id": os.environ["MAALDAR_ROLE_ID"],
		"custom_role_id": os.environ["CUSTOM_ROLE_ID"],
		"staff_role_id": os.environ["STAFF_ROLE_ID"],
		"users_ids":	os.environ["USERS_IDS"].split(", "),
		"guild_id": os.environ["GUILD_ID"],
		"role_ids": os.environ["ROLE_IDS"].split(", "),
		"database_name": os.environ["DATABASE_NAME"],
		"database_user": os.environ["DATABASE_USER"],
		"database_password": os.environ["DATABASE_PASSWORD"],
		"database_host": os.environ["DATABASE_HOST"],
		"database_port": os.environ["DATABASE_PORT"],
		"token": os.environ["TOKEN"]
	}

def check_if_user_exists(cursor: Cursor, user_id):
	cursor.execute(
			f"SELECT * FROM Maaldar WHERE user_id = {user_id}"
	)
	return cursor.fetchone()

def make_image(dominant_color):
	image = Image.new(mode="RGBA", size=(50, 50),
										color=(0, 0, 0, 0))
	ImageDraw.Draw(image).rounded_rectangle(
			(0, 0, 50, 50), 
			radius=20,
			fill=dominant_color
	)

	return image

def clean_up():
	if os.path.exists("palette.png"):
			os.remove("palette.png")

def concatenate_images(images):
	"""size = width of 10 images and height of 1 image"""
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
		font = ImageFont.truetype("arial.ttf", 13)
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

	image.save("palette.png", "PNG")

def rgb_to_hex(rgb):
    return "%02x%02x%02x" % (rgb)

def match_url_regex(string):
    # It works 🤷‍♀️
    return re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', string)

class Dropdown(discord.ui.Select):
	def __init__(self, assignee, role):
		self.assignee = assignee
		self.role = role

		options = [
			discord.SelectOption(
				label="Yes", 
				description="I want the role (I love them)", 
				emoji='✅'
			),
			discord.SelectOption(
				label="No", 
				description="I do not want the role (I hate them)", 
				emoji='❎'
			)
		]

		super().__init__(
			placeholder="Choose whether you'd like the role",
			min_values=1,
			max_values=1,
			options=options
		)

	async def callback(self, interaction: discord.Interaction):
		try:
			if not interaction.user == self.assignee:
				return
				
			if self.values[0] == "Yes":
				await self.assignee.add_roles(self.role)
				await interaction.response.send_message("The role has been assigned to you 🎉")

			if self.values[0] == "No":
				await interaction.response.send_message("They hate you 😢")

			await self.view.stop()

		except TypeError:
			pass


class DropdownView(discord.ui.View):
	def __init__(self, assignee, role):
		super().__init__()

		self.add_item(Dropdown(assignee, role))
