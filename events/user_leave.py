import discord
from discord.ext import commands

from util import configuration, select_one, delete_query

class UserLeaveEvent(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  @commands.Cog.listener()
  async def on_member_remove(self, member):
    guild: discord.Guild = member.guild
    
    maaldar_user = select_one(f"SELECT * FROM Maaldar WHERE user_id = '{member.id}'")
    if maaldar_user is None:
      return
    
    delete_query(f"DELETE FROM Maaldar WHERE user_id = '{member.id}'")
    
    role = guild.get_role(int(maaldar_user[1]))
    await role.delete()

async def setup(bot: commands.Bot):
  await bot.add_cog(UserLeaveEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
