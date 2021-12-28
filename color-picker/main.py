import json
import sqlite3
import asyncio

from quart import Quart, render_template, request
import discord

"""Quart app"""
quart_app = Quart(__name__)
"""Get event loop for Quart app"""
quart_event_loop = asyncio.get_event_loop()

"""Bot initialize"""
intents = discord.Intents(members=True, guilds=True)
bot = discord.Bot(intents=intents)

"""Database initialize"""
connection = sqlite3.connect("../maaldar.db")
cursor = connection.cursor()


"""Main route"""


@quart_app.route("/<token>")
async def main_route(token):
    await bot.wait_until_ready()

    cursor.execute("SELECT * FROM MaaldarSession WHERE token = ?", (token, ))
    maaldar_session = cursor.fetchone()
    if maaldar_session:
        cursor.execute("SELECT role_id FROM Maaldar WHERE user_id = ?",
                       (maaldar_session[0], ))

        guild = bot.get_guild(268597766652035072)
        role_id = cursor.fetchone()[0]
        member = guild.get_member(int(maaldar_session[0]))
        role = guild.get_role(int(role_id))

        return await render_template("index.html",
                                     name=member.name,
                                     avatar_url=member.avatar.url,
                                     role_id=role_id,
                                     token=token,
                                     color=role.color)

    return f"<p>Token invalid</p>"


@quart_app.route("/set_role_color", methods=["POST"])
async def set_role_color():
    bytes_data = await request.body
    data = json.loads(bytes_data.decode("UTF-8"))

    token = data["token"]
    cursor.execute("SELECT * FROM MaaldarSession WHERE token = ?", (token, ))
    maaldar_session = cursor.fetchone()
    if not maaldar_session:
        return "Invalid token"

    await bot.wait_until_ready()
    guild = bot.get_guild(268597766652035072)
    role = guild.get_role(int(data["role_id"]))
    color = data["color"]

    await role.edit(
        color=discord.Color(
            int(color[1:], 16)
        )
    )

    return "ok"

"""Start bot and add it to Quart app loop"""
bot_app = bot.start(open("./token.txt").read())
bot_task = asyncio.ensure_future(bot_app)

"""Run quart app with the Quart app loop"""
quart_app.run(loop=quart_event_loop, port=3000)
