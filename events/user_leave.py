import sqlite3

import discord
from discord.ext import commands

from util import configuration

class UserLeaveEvent(commands.Cog):
  connection = sqlite3.connect("maaldar.db")
  cursor = connection.cursor()

  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_member_remove(self, member):
    guild: discord.Guild = member.guild

    UserLeave.cursor.execute(
      f"SELECT * FROM Maaldar WHERE user_id = {member.id}"
    )
    maaldar_user = UserLeave.cursor.fetchone()
    if maaldar_user is None:
      return

    UserLeave.cursor.execute(
      "DELETE FROM Maaldar WHERE user_id = ?", (member.id, )
    )
    UserLeave.connection.commit()

    role = guild.get_role(int(maaldar_user[1]))
    await role.delete()


async def setup(bot: commands.Bot):
  await bot.add_cog(UserLeaveEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
