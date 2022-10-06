import sqlite3

import discord
from discord.ext import commands

from util import configuration


class RoleRemove(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        RoleRemove.cursor.execute(f"SELECT * FROM Maaldar WHERE role_id = {role.id}")
        maaldar_role = RoleRemove.cursor.fetchone()
        if maaldar_role is None:
            return

        RoleRemove.cursor.execute("DELETE FROM Maaldar WHERE role_id = ?", (role.id,))
        RoleRemove.connection.commit()
        print("Deleted role from Maaldar that was manually deleted")


async def setup(bot: commands.Bot):
    await bot.add_cog(
        RoleRemove(bot), guilds=[discord.Object(id=configuration["guild_id"])]
    )
