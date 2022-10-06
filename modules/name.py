import sqlite3
from sqlite3.dbapi2 import connect

from discord.commands import Option
from discord.commands import permissions
from discord.ext import commands

from main import maaldar
from util import check_if_user_exists
from util import configuration


class Name(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    def __init__(self, bot):
        self.bot = bot

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def name(ctx, new_name: Option(str, "New name for your role", required=True)):
        """Sets a new name for your role"""

        if len(new_name) > 100:
            await ctx.respond(
                "🤔 I wouldn't do that\n" "> Role name must be fewer than 100 characters"
            )
            return

        maaldar_user = check_if_user_exists(Name.cursor, ctx.author.id)
        if maaldar_user is None:
            await ctx.respond(
                "You do not have a role yet.\n" "> Make one by typing `/maaldar create`"
            )
            return

        role = ctx.guild.get_role(int(maaldar_user[1]))
        await role.edit(name=new_name)

        await ctx.respond(f"Role name set to **{new_name}** ✨")


def setup(bot):
    bot.add_cog(Name(bot))
