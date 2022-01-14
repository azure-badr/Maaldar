import discord
from discord.ext import commands
from discord.commands import permissions, Option

from util import configuration, check_if_user_exists
from main import maaldar

import uuid
import asyncio
import sqlite3


class Color(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    @staticmethod
    async def create_session(ctx):
        session = uuid.uuid4().hex
        Color.cursor.execute(
            "INSERT INTO MaaldarSession VALUES (?, ?)", (
                ctx.author.id, session)
        )
        Color.connection.commit()
        await ctx.respond("Created session, please check your DM")

        try:
            await ctx.author.send("Session created ✨\n"
                                  f"> http://pakcord.mooo.com/{session}")
            """Wait for 1 hour and delete session"""
            await asyncio.sleep(3600)
            Color.cursor.execute(
                "DELETE FROM MaaldarSession WHERE user_id = ?", (
                    ctx.author.id, )
            )
            Color.connection.commit()

        except discord.Forbidden:
            await ctx.respond("Please enable your DMs")
            Color.cursor.execute(
                "DELETE FROM MaaldarSession WHERE user_id = ?", (
                    ctx.author.id, )
            )
            Color.connection.commit()

    def __init__(self, bot):
        self.bot = bot

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def color(ctx, new_color: Option(str, "New color for your role (e.g #000000)", required=False)):
        """Sets a new color for your role"""

        maaldar_user = check_if_user_exists(Color.cursor, ctx.author.id)
        if maaldar_user is None:
            await ctx.respond("You do not have a role yet.\n"
                              "> Make one by typing `/maaldar create`")
            return

        if not new_color:
            role = ctx.guild.get_role(int(maaldar_user[1]))
            await role.edit(color=discord.Color.default())
            
            await ctx.respond("Role color set to default")
            return
        
            """@TODO implemenet a better system for color_picker website"""
            Color.cursor.execute(
                "SELECT * FROM MaaldarSession WHERE user_id = ?", (ctx.author.id, ))
            maaldar_session = Color.cursor.fetchone()
            if not maaldar_session:
                asyncio.ensure_future(
                    Color.create_session(ctx))

                return

            await ctx.respond(f"Session already exists {maaldar_session[1]}")
            return

        new_color = new_color[1:] if new_color.startswith("#") else new_color

        try:
            new_color = int(new_color, 16)
        except ValueError:
            await ctx.respond("Please enter the hex value for your color")
            return

        role = ctx.guild.get_role(int(maaldar_user[1]))
        try:
            await role.edit(color=discord.Color(new_color))
        except:
            await ctx.respond("Please enter a valid hex value\n"
                              "> Use Google color picker and copy the HEX value")
            return

        await ctx.respond(f"New role color set ✨")


def setup(bot):
    bot.add_cog(Color(bot))
