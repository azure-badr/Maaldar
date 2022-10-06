import discord
from discord.ext import commands

from util import configuration
from database.db import database

class UserLeaveEvent(commands.Cog):
  connection = database.connection
  cursor = database.cursor

  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_member_remove(self, member):
    guild: discord.Guild = member.guild

    UserLeaveEvent.cursor.execute(
      f"SELECT * FROM Maaldar WHERE user_id = '{member.id}'"
    )
    maaldar_user = UserLeaveEvent.cursor.fetchone()
    if maaldar_user is None:
      return

    UserLeaveEvent.cursor.execute(
      f"DELETE FROM Maaldar WHERE user_id = '{member.id}'"
    )
    UserLeaveEvent.connection.commit()

    role = guild.get_role(int(maaldar_user[1]))
    await role.delete()


async def setup(bot: commands.Bot):
  await bot.add_cog(UserLeaveEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
