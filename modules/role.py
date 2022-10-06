import sqlite3
from sqlite3.dbapi2 import connect

from discord.commands import Option
from discord.commands import permissions
from discord.ext import commands

from main import maaldar
from util import check_if_user_exists
from util import configuration


class Role(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    def __init__(self, bot):
        self.bot = bot

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def create(ctx, name: Option(str, "Name of your role", required=True)):
        """Creates a new role for you"""

        maaldar_user = check_if_user_exists(Role.cursor, ctx.author.id)
        if maaldar_user is None:
            await ctx.defer()

            guild = ctx.guild
            role = await guild.create_role(name=name)
            await role.edit(position=configuration["role_position"])
            await ctx.author.add_roles(role)

            Role.cursor.execute(
                "INSERT INTO Maaldar VALUES (?, ?)", (ctx.author.id, role.id)
            )
            Role.connection.commit()

            await ctx.send_followup(f"**{name}** created and assigned to you ✨")
            return

        role = ctx.guild.get_role(int(maaldar_user[1]))
        await ctx.respond(
            f"Your role already exists by the name `{role.name}`\n"
            "> Assign it to yourself by typing `/maaldar assign`"
        )


def setup(bot):
    bot.add_cog(Role(bot))
