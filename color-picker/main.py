# Hypercorn
from hypercorn.asyncio import serve
from hypercorn.config import Config

import json
import asyncio

import discord
from discord.ext import commands

from quart import Quart, render_template, request
import sys
import os.path

from config import configuration
# Setting up the static files and templates
sys.path.append(
  os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir)
  )
)

# Setup database
import psycopg2
connection = psycopg2.connect(
  database=configuration["database_name"], 
  user=configuration["database_user"], 
  password=configuration["database_password"],
  host=configuration["database_host"], 
  port=configuration["database_port"]
)
cursor = connection.cursor()

# Quart app
quart_app = Quart(__name__)
# Get event loop for Quart app
quart_event_loop = asyncio.get_event_loop()

# Bot initialize
intents = discord.Intents(members=True, guilds=True)
bot = commands.Bot(command_prefix='', intents=intents)

@quart_app.route("/")
async def main():
  return "<h1>Hello world</h1>"

@quart_app.route("/<token>")
async def main_route(token):
  await bot.wait_until_ready()

  cursor.execute(f"SELECT * FROM MaaldarSession WHERE token = '{token}'")
  maaldar_session = cursor.fetchone()
  if maaldar_session:
    cursor.execute(
      f"SELECT role_id FROM Maaldar WHERE user_id = '{maaldar_session[0]}'"
    )

    guild = bot.get_guild(configuration["guild_id"])
    role_id = cursor.fetchone()[0]
    member = guild.get_member(int(maaldar_session[0]))
    role = guild.get_role(int(role_id))
    role_icon = role.icon.url if role.icon else None

    return await render_template(
      "index.html",
      name=member.name,
      avatar_url=member.avatar.url,
      role_icon=role_icon,
      role_id=role_id,
      token=token,
      color=role.color
    )

  return f"<p>Token invalid</p>"

@quart_app.route("/set_role_color", methods=["POST"])
async def set_role_color():
  bytes_data = await request.body
  data = json.loads(bytes_data.decode("UTF-8"))
  token = data["token"]
  cursor.execute(f"SELECT * FROM MaaldarSession WHERE token = '{token}'")
  maaldar_session = cursor.fetchone()
  if not maaldar_session:
    return "Invalid token", 403
  
  """Validate role ID being provided in the body"""
  user_id = maaldar_session[0]
  cursor.execute(f"SELECT role_id FROM Maaldar WHERE user_id = '{user_id}'")
  role_id = cursor.fetchone()[0]

  if role_id != data["role_id"]:
    return "Token doesn't match your role ID", 403

  await bot.wait_until_ready()
  guild = bot.get_guild(configuration["guild_id"])
  role = guild.get_role(int(data["role_id"]))
  color = data["color"]
  try:
    await role.edit(
      color=discord.Color(int(color[1:], 16))
    )
  except:
    return "Invalid color", 422

  return "Role set", 200

# Start bot and add it to Quart app loop
bot_app = bot.start(configuration["token"])
bot_task = asyncio.ensure_future(bot_app)

# Run quart app with the Quart app loop
# quart_app.run(loop=quart_event_loop, port=3000)
quart_event_loop.run_until_complete(serve(quart_app, Config()))