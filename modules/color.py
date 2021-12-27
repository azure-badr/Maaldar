import discord
from discord.ext import commands
from discord.commands import permissions, Option

from util import configuration
from main import maaldar

import sqlite3


class Color(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    def __init__(self, bot):
        self.bot = bot

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def color(ctx, new_color: Option(str, "New color for your role (e.g #000000)", required=True)):
        """Sets a new color for your role"""

        new_color = new_color[1:] if new_color.startswith("#") else new_color

        Color.cursor.execute(
            f"SELECT * FROM Maaldar WHERE user_id = {ctx.author.id}"
        )
        maaldar_user = Color.cursor.fetchone()
        if maaldar_user is None:
            await ctx.respond("You do not have a role yet.\n"
                              "> Make one by typing `/maaldar create`")
            return

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
