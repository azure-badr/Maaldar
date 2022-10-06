import asyncio
import json
import os.path
import sqlite3
import sys

from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart
from quart import render_template
from quart import request

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
import discord
from discord.ext import commands

# Quart app
quart_app = Quart(__name__)

# Get event loop for Quart app
quart_event_loop = asyncio.get_event_loop()

# Bot initialize
intents = discord.Intents(members=True, guilds=True)
bot = commands.Bot(command_prefix="", intents=intents)

# Database initialize
connection = sqlite3.connect("../maaldar.db")
cursor = connection.cursor()

# Main route


@quart_app.route("/<token>")
async def main_route(token):
    await bot.wait_until_ready()

    cursor.execute("SELECT * FROM MaaldarSession WHERE token = ?", (token,))
    maaldar_session = cursor.fetchone()
    if maaldar_session:
        cursor.execute(
            "SELECT role_id FROM Maaldar WHERE user_id = ?", (maaldar_session[0],)
        )

        guild = bot.get_guild(268597766652035072)
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
            color=role.color,
        )

    return f"<p>Token invalid</p>"


@quart_app.route("/set_role_color", methods=["POST"])
async def set_role_color():
    bytes_data = await request.body
    data = json.loads(bytes_data.decode("UTF-8"))

    token = data["token"]
    cursor.execute("SELECT * FROM MaaldarSession WHERE token = ?", (token,))
    maaldar_session = cursor.fetchone()
    if not maaldar_session:
        return "Invalid token", 401

    """Validate role ID being provided in the body"""
    user_id = maaldar_session[0]
    cursor.execute("SELECT role_id FROM Maaldar WHERE user_id = ?", (user_id,))
    role_id = cursor.fetchone()[1]

    if role_id != int(data["role_id"]):
        return "Token doesn't match your role ID", 401

    await bot.wait_until_ready()
    guild = bot.get_guild(268597766652035072)
    role = guild.get_role(int(data["role_id"]))
    color = data["color"]
    try:
        await role.edit(color=discord.Color(int(color[1:], 16)))
    except:
        return "Invalid color", 400

    return "Role set", 200


# Start bot and add it to Quart app loop
bot_app = bot.start(open("./token.txt").read())
bot_task = asyncio.ensure_future(bot_app)

# Run quart app with the Quart app loop
# quart_app.run(loop=quart_event_loop, port=3000)
quart_event_loop.run_until_complete(serve(quart_app, Config()))
