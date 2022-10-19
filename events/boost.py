import discord
from discord.ext import commands

from util import configuration
from database.db import database

class BoostEvent(commands.Cog):
  connection = database.connection
  cursor = database.cursor

  def __init__(self, bot):
    self.bot = bot
  
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
    
    if before.premium_since is not None and after.premium_since is None:
      # Setting member.premium_since.tzinfo to None to avoid naive and aware datetime comparison
      boosting_since = before.premium_since.replace(tzinfo=None)
      self.cursor.execute(f"SELECT * FROM MaaldarDuration WHERE user_id = '{member.id}'")
      if self.cursor.fetchone() is None:
        self.cursor.execute(
          f"INSERT INTO MaaldarDuration VALUES ('{member.id}', '{boosting_since}')"
        )
        self.connection.commit()
        return

      self.cursor.execute(
        f"UPDATE MaaldarDuration SET boosting_since = boosting_since + '{boosting_since}' "
        f"WHERE user_id = '{member.id}'"
      )
      self.connection.commit()
    

async def setup(bot: commands.Bot):
  await bot.add_cog(BoostEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
