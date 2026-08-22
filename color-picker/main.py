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

from config import (
  configuration,
  select_one,
  get_dominant_colors,
  fetch_image_from_url,
  decode_image_data_uri,
  sniff_image_type,
  MAX_ICON_BYTES,
  MAX_SOURCE_BYTES,
)
sys.path.append(
  os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir)
  )
)

def static_version(filename):
  """Fingerprint for a static file, used to bust the browser cache.

  Static files are served with a 12 hour max-age, so without this a CSS
  change isn't picked up until the cache expires or the user hard refreshes.
  """
  try:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", filename)
    return str(int(os.path.getmtime(path)))
  except OSError:
    return "0"


quart_app = Quart(__name__)
# A 256 KB icon is ~350 KB once base64-encoded; cap the body well above that
# but far below anything that could exhaust memory.
quart_app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
quart_event_loop = asyncio.get_event_loop()

intents = discord.Intents(members=True, guilds=True)
bot = commands.Bot(command_prefix='', intents=intents)

async def get_guild():
  await bot.wait_until_ready()
  return bot.get_guild(configuration["guild_id"])

# Fire-and-forget tasks are garbage collected if nothing holds a reference to
# them mid-flight, so keep one until they finish.
background_tasks = set()


def run_in_background(coroutine):
  """Schedule work on the shared event loop without blocking the response.

  Not a thread: discord.py's HTTP client is asyncio-based and not thread-safe,
  and the bot already shares this loop with Quart.
  """
  task = asyncio.ensure_future(coroutine)
  background_tasks.add(task)
  task.add_done_callback(background_tasks.discard)
  return task


async def send_botspam(message):
  """Post an action to the log channel.

  Logging must never break the request that triggered it, so every failure
  here is reported to stdout and swallowed.
  """
  channel_id = configuration.get("botspam_channel_id")
  if not channel_id:
    return

  try:
    channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
    # Mentions render as names, but a log line shouldn't notify the user or
    # everyone holding the role.
    await channel.send(message, allowed_mentions=discord.AllowedMentions.none())
  except Exception as error:
    print(f"Could not log to botspam channel: {error}")


async def log_color_change(member, role, color_int, secondary_color_int):
  try:
    who = member.mention if member else "Someone"

    if secondary_color_int is not None:
      detail = f"a gradient on {role.mention}: `#{color_int:06X}` to `#{secondary_color_int:06X}`"
    else:
      detail = f"a solid color on {role.mention}: `#{color_int:06X}`"

    await send_botspam(f"{who} set {detail}")
  except Exception as error:
    print(f"Could not build color log: {error}")


async def log_icon_change(member, role, removed, cropped):
  try:
    who = member.mention if member else "Someone"

    if removed:
      action = "removed the icon from"
    elif cropped:
      action = "set a cropped icon on"
    else:
      action = "set an icon on"

    await send_botspam(f"{who} {action} {role.mention}")
  except Exception as error:
    print(f"Could not build icon log: {error}")


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
  
  name = member.display_name
  avatar_url = member.display_avatar.url
  role_icon = role.icon.url if role.icon else None

  # Server tag: the little badge and text Discord shows after the name, ahead
  # of the role icon. identity_enabled is None when the user has a primary
  # guild but hasn't reaffirmed it after a change, so only an explicit False
  # counts as hidden.
  primary_guild = member.primary_guild
  server_tag = (
    primary_guild.tag
    if primary_guild and primary_guild.identity_enabled is not False
    else None
  )
  server_tag_badge = (
    primary_guild.badge.url if server_tag and primary_guild.badge else None
  )
  color = role.color
  secondary_color = role.secondary_color

  return await render_template(
    "index.html",
    css_version=static_version("index.css"),
    name=name,
    avatar_url=avatar_url,
    role_icon=role_icon,
    server_tag=server_tag,
    server_tag_badge=server_tag_badge,
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
  
  secondary_color_int = None

  try:
    color = data["color"]
    color_int = int(color[1:], 16) if color.startswith("#") else int(color, 16)
    
    edit_params = {"color": discord.Color(color_int)}
    
    if "secondary_color" in data and data["secondary_color"]:
      secondary_color = data["secondary_color"]
      secondary_color_int = int(secondary_color[1:], 16) if secondary_color.startswith("#") else int(secondary_color, 16)
      edit_params["secondary_color"] = discord.Color(secondary_color_int)
    
    await role.edit(**edit_params)
  except Exception as e:
    return f"Invalid color format: {str(e)}", 422

  # Logged outside the try so a logging failure can't be reported as a bad
  # color, and in the background so it doesn't delay the response.
  run_in_background(
    log_color_change(guild.get_member(int(user_id)), role, color_int, secondary_color_int)
  )

  return "Role color set", 200

@quart_app.route("/set_role_icon", methods=["POST"])
async def set_role_icon():
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

  if "ROLE_ICONS" not in guild.features:
    return "This server hasn't unlocked role icons (needs Level 2 boosts)", 403

  # display_icon=None removes the icon; anything else has to be raw PNG/JPEG
  # bytes, so resolve whichever source the user gave us down to that.
  icon = None

  if not data.get("remove"):
    try:
      if data.get("image"):
        icon = decode_image_data_uri(data["image"])
      elif data.get("url"):
        icon = await fetch_image_from_url(data["url"])
      else:
        return "No image provided", 400
    except ValueError as error:
      return str(error), 400

    if len(icon) > MAX_ICON_BYTES:
      return "Image is larger than 256 KB", 400

    if sniff_image_type(icon) not in ("png", "jpeg"):
      return "Only PNG and JPEG images are supported", 400

  try:
    updated_role = await role.edit(display_icon=icon)
  except discord.Forbidden:
    return "The bot doesn't have permission to edit this role", 403
  except discord.HTTPException as error:
    return f"Discord rejected the icon: {error.text}", 400

  run_in_background(
    log_icon_change(
      guild.get_member(int(user_id)),
      updated_role or role,
      icon is None,
      bool(data.get("cropped")),
    )
  )

  return "Role icon removed" if icon is None else "Role icon set", 200

@quart_app.route("/proxy_image", methods=["GET"])
async def proxy_image():
    """Re-serve a remote image from our own origin.

    The cropper has to read an image's pixels back out of a canvas, which the
    browser forbids for cross-origin images. Passing the bytes through here
    makes them same-origin, so a linked image or the role's existing icon can
    be cropped the same way an upload is.
    """
    token = request.args.get("token")
    url = request.args.get("url")

    user_data = select_one("SELECT user_id FROM MaaldarSession WHERE token = %s", (token,))
    if not user_data:
      return "Invalid token", 403

    if not url:
      return "No image link provided", 400

    try:
      data = await fetch_image_from_url(url, MAX_SOURCE_BYTES)
    except ValueError as error:
      return str(error), 400

    image_type = sniff_image_type(data)
    if image_type is None:
      return "That link isn't a PNG, JPEG, GIF or WebP image", 400

    # Pin the content type to what the bytes actually are and forbid sniffing,
    # so this can't be turned into a way to serve active content from our
    # origin. The CSP keeps the response inert even if it's opened directly.
    return data, 200, {
      "Content-Type": f"image/{image_type}",
      "X-Content-Type-Options": "nosniff",
      "Content-Security-Policy": "default-src 'none'; sandbox",
      "Cache-Control": "private, max-age=300",
    }

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
    
    avatar_url = member.display_avatar.url
    
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