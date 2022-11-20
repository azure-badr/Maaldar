import discord
from discord.ext import commands

from util import configuration, select_one, delete_query

class RoleRemove(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  @commands.Cog.listener()
  async def on_guild_role_delete(self, role):
    maaldar_role = select_one(f"SELECT * FROM Maaldar WHERE role_id = '{role.id}'")
    if maaldar_role is None:
      return
    
    delete_query(f"DELETE FROM Maaldar WHERE role_id = '{role.id}'")
    print("Deleted role from Maaldar that was manually deleted")


async def setup(bot: commands.Bot):
  await bot.add_cog(RoleRemove(bot), guilds=[discord.Object(id=configuration["guild_id"])])
