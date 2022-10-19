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
    if before.premium_since is not None and after.premium_since is None:
      pass
    

async def setup(bot: commands.Bot):
  await bot.add_cog(BoostEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
