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
sys.path.append(
  os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir)
  )
)

quart_app = Quart(__name__)
quart_event_loop = asyncio.get_event_loop()

intents = discord.Intents(members=True, guilds=True)
bot = commands.Bot(command_prefix='', intents=intents)

async def get_guild():
  await bot.wait_until_ready()
  return bot.get_guild(configuration["guild_id"])

@quart_app.route("/")
async def main():
  return "<h1>Hello world</h1>"

@quart_app.route("/<token>")
async def main_route(token):
  user_data = select_one("""
    SELECT ms.user_id, m.role_id 
    FROM MaaldarSession ms 
    JOIN Maaldar m ON ms.user_id = m.user_id 
    WHERE ms.token = %s
  """, (token,))
  
  if not user_data:
    return "<p>Token invalid</p>"
  
  user_id, role_id = user_data
  
  guild = await get_guild()
  
  if not guild:
    return "<p>Guild not found</p>"
  
  member = guild.get_member(int(user_id))
  role = guild.get_role(int(role_id))

  if not member or not role:
    return "<p>Member or role not found</p>"
  
  name = member.nick if member.nick else member.name
  avatar_url = member.guild_avatar.url if member.guild_avatar else member.avatar.url
  role_icon = role.icon.url if role.icon else None
  color = role.color
  secondary_color = role.secondary_color

  return await render_template(
    "index.html",
    name=name,
    avatar_url=avatar_url,
    role_icon=role_icon,
    role_id=role_id,
    token=token,
    color=color,
    secondary_color=secondary_color,
  )

@quart_app.route("/set_role_color", methods=["POST"])
async def set_role_color():
  bytes_data = await request.body
  data = json.loads(bytes_data.decode("UTF-8"))
  token = data["token"]
  
  user_data = select_one("""
    SELECT ms.user_id, m.role_id 
    FROM MaaldarSession ms 
    JOIN Maaldar m ON ms.user_id = m.user_id 
    WHERE ms.token = %s
  """, (token,))

  if not user_data:
    return "Invalid token", 403
  
  user_id, role_id = user_data
  
  if role_id != data["role_id"]:
    return "Token doesn't match your role ID", 403

  guild = await get_guild()
  
  role = guild.get_role(int(data["role_id"]))
  if not role:
    return "Role not found", 404
  
  if len(role.members) > 1 and "secondary_color" in data:
    return "Cannot set gradient for shared role", 403
  
  try:
    color = data["color"]
    color_int = int(color[1:], 16) if color.startswith("#") else int(color, 16)
    
    edit_params = {"color": discord.Color(color_int)}
    
    if "secondary_color" in data and data["secondary_color"]:
      secondary_color = data["secondary_color"]
      secondary_color_int = int(secondary_color[1:], 16) if secondary_color.startswith("#") else int(secondary_color, 16)
      edit_params["secondary_color"] = discord.Color(secondary_color_int)
    
    await role.edit(**edit_params)
    
    return "Role color set", 200
  except Exception as e:
    return f"Invalid color format: {str(e)}", 422

@quart_app.route("/get_dominant_colors", methods=["GET"])
async def get_dominant_colors_api():
    token = request.args.get("token")
    
    user_data = select_one("SELECT user_id FROM MaaldarSession WHERE token = %s", (token,))
    if not user_data:
      return "Invalid token", 403
    
    user_id = user_data[0]
    
    guild = await get_guild()
    
    member = guild.get_member(int(user_id))
    if not member:
      return "Member not found", 404
    
    avatar_url = member.guild_avatar.url if member.guild_avatar else member.avatar.url
    
    try:
      dominant_colors = await get_dominant_colors(avatar_url)
      return {"dominant_colors": dominant_colors}
    except Exception as e:
      return f"Error extracting colors: {str(e)}", 500



# Start bot and add it to Quart app loop
bot_app = bot.start(configuration["token"])
bot_task = asyncio.ensure_future(bot_app)

# Run quart app with the Quart app loop
# quart_app.run(loop=quart_event_loop, port=3000)
config = Config()
config.bind = ["0.0.0.0:8080"]
quart_event_loop.run_until_complete(serve(quart_app, config))