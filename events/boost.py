import discord
from discord.ext import commands

from util import configuration
from database.db import database

from datetime import datetime, timedelta

class BoostEvent(commands.Cog):
  DAYS_REQUIRED_FOR_ROLE = 180
  
  connection = database.connection
  cursor = database.cursor

  def __init__(self, bot):
    self.bot = bot
  
  def _check_and_update_duration(self, member_id: str, boosting_since: timedelta) -> None:
    self.cursor.execute(f"SELECT * FROM MaaldarDuration WHERE user_id = '{member_id}'")
    if self.cursor.fetchone() is None:
      self.cursor.execute(
        f"INSERT INTO MaaldarDuration VALUES ('{member_id}', '{boosting_since}')"
      )
      self.connection.commit()
      return
    
    self.cursor.execute(
      f"UPDATE MaaldarDuration SET boosting_since = boosting_since + '{boosting_since}' "
      f"WHERE user_id = '{member_id}'"
    )
    self.connection.commit()
  
  @commands.Cog.listener()
  async def on_member_update(self, before: discord.Member, after: discord.Member):
    member = before

    # @DEVELOPMENT - This is for testing purposes only
    # guild = before.guild
    # maaldar_role = guild.get_role(configuration["custom_role_id"])
    # if maaldar_role not in after.roles and maaldar_role in before.roles:
    #   self.cursor.execute(
    #     f"UPDATE MaaldarDuration SET boosting_since = boosting_since + '115 days, 7:07:47.776831' "
    #     f"WHERE user_id = '{member.id}'"
    #   )
    #   self.connection.commit()
    
    # If member was not boosting before, return
    if before.premium_since is None:
      return
    
    # If member was boosting after, return
    if after.premium_since is not None:
      return
    
    # Setting member.premium_since.tzinfo to None to avoid naive and aware datetime comparison
    boosting_since = datetime.now() - before.premium_since.replace(tzinfo=None)
    self._check_and_update_duration(member.id, boosting_since)
    
    self.cursor.execute(f"SELECT boosting_since FROM MaaldarDuration WHERE user_id = '{member.id}'")
    boosting_since = self.cursor.fetchone()[0] # timedelta object
    
    if boosting_since >= timedelta(days=self.DAYS_REQUIRED_FOR_ROLE):
      return
    
    self.cursor.execute(f"SELECT role_id FROM Maaldar WHERE user_id = '{member.id}'")
    if self.cursor.fetchone() is None:
      return
    
    role_id = self.cursor.fetchone()[0]
    role = member.guild.get_role(int(role_id))

    await member.remove_roles(role)
    self.cursor.execute(f"DELETE FROM Maaldar WHERE user_id = '{member.id}'")
    self.cursor.execute(f"DELETE FROM MaaldarDuration WHERE user_id = '{member.id}'")
    self.connection.commit()

async def setup(bot: commands.Bot):
  await bot.add_cog(BoostEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
