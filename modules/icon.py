import sqlite3

import aiohttp
import discord
from discord.commands import Option
from discord.commands import permissions
from discord.ext import commands

from main import maaldar
from util import check_if_user_exists
from util import configuration
from util import match_url_regex


class Icon(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    def __init__(self, bot):
        self.bot = bot

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def icon(
        ctx,
        url: Option(
            str, "URL link to the icon (must be in PNG/JPG format)", required=False
        ),
    ):
        """Sets an icon for your role. If the url is not provided, it removes the icon"""

        maaldar_user = check_if_user_exists(Icon.cursor, ctx.author.id)
        if maaldar_user is None:
            await ctx.respond(
                "You do not have a role yet.\n" "> Make one by typing `/maaldar create`"
            )
            return

        role: discord.Role = ctx.guild.get_role(int(maaldar_user[1]))

        if not url:
            await role.edit(icon=None)
            await ctx.respond("Role icon removed 🗑️")
            return

        if not match_url_regex(url):
            await ctx.respond("Enter a valid URL path!\n> It must end in .png or .jpg")
            return

        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    try:
                        await role.edit(icon=await response.read())
                        await ctx.send_followup("Role icon set ✨")
                        return

                    except Exception as error:
                        await ctx.send_followup(error)
                        return

                await ctx.send_followup(
                    "Something is wrong with the website. Try a different one 👉"
                )


def setup(bot):
    bot.add_cog(Icon(bot))
