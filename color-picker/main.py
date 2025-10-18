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

from config import configuration, select_one, get_dominant_colors
# Setting up the static files and templates
sys.path.append(
  os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir)
  )
)

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

  maaldar_session = select_one("SELECT * FROM MaaldarSession WHERE token = %s", (token,))
  if maaldar_session:
    guild = bot.get_guild(configuration["guild_id"])
    role_id = select_one("SELECT role_id FROM Maaldar WHERE user_id = %s", (maaldar_session[0], ))[0]
    member = guild.get_member(int(maaldar_session[0]))
    role = guild.get_role(int(role_id))

    if not role:
      return "<p>Role not found</p>"
    
    role_icon = role.icon.url if role.icon else None

    dominant_colors = await get_dominant_colors(member.avatar.url)

    return await render_template(
      "index.html",
      name=member.nick if member.nick else member.name,
      avatar_url=member.guild_avatar.url if member.guild_avatar else member.avatar.url,
      role_icon=role_icon,
      role_id=role_id,
      token=token,
      color=role.color,
      dominant_colors=dominant_colors
    )

  return f"<p>Token invalid</p>"

@quart_app.route("/set_role_color", methods=["POST"])
async def set_role_color():
  bytes_data = await request.body
  data = json.loads(bytes_data.decode("UTF-8"))
  token = data["token"]
  maaldar_session = select_one("SELECT * FROM MaaldarSession WHERE token = %s", (token,))

  if not maaldar_session:
    return "Invalid token", 403
  
  """Validate role ID being provided in the body"""
  user_id = maaldar_session[0]
  role_id = select_one("SELECT role_id FROM Maaldar WHERE user_id = %s", (user_id, ))[0]
  
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

@quart_app.route("/set_role_gradient", methods=["POST"])
async def set_role_gradient():
  bytes_data = await request.body
  data = json.loads(bytes_data.decode("UTF-8"))
  token = data["token"]
  maaldar_session = select_one("SELECT * FROM MaaldarSession WHERE token = %s", (token,))

  if not maaldar_session:
    return "Invalid token", 403
  
  """Validate role ID being provided in the body"""
  user_id = maaldar_session[0]
  role_id = select_one("SELECT role_id FROM Maaldar WHERE user_id = %s", (user_id, ))[0]
  
  if role_id != data["role_id"]:
    return "Token doesn't match your role ID", 403

  await bot.wait_until_ready()
  guild = bot.get_guild(configuration["guild_id"])
  role = guild.get_role(int(data["role_id"]))
  
  # Check if role has multiple members (can't set gradient if shared)
  if len(role.members) > 1:
    return "Cannot set gradient for shared role", 403
  
  color = data["color"]
  secondary_color = data["secondary_color"]
  
  try:
    # Convert hex colors to integers
    color_int = int(color[1:], 16) if color.startswith("#") else int(color, 16)
    secondary_color_int = int(secondary_color[1:], 16) if secondary_color.startswith("#") else int(secondary_color, 16)
    
    await role.edit(
      color=discord.Color(color_int),
      secondary_color=discord.Color(secondary_color_int)
    )
  except:
    return "Invalid color format", 422
  
  return "Gradient set", 200

# Start bot and add it to Quart app loop
bot_app = bot.start(configuration["token"])
bot_task = asyncio.ensure_future(bot_app)

# Run quart app with the Quart app loop
# quart_app.run(loop=quart_event_loop, port=3000)
config = Config()
config.bind = ["0.0.0.0:8080"]
quart_event_loop.run_until_complete(serve(quart_app, config))