import discord
from discord.ext import commands

from util import *

class MaaldarBot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix='', intents=intents)
    
    async def on_ready(self) -> None:
      await self.wait_until_ready()
      await self.tree.sync(guild=discord.Object(id=configuration["guild_id"]))

    async def setup_hook(self) -> None:
      await self.load_extension("events.boost")
      await self.load_extension("events.user_leave")
      await self.load_extension("events.role_remove")

      await self.load_extension("modules.maaldar")

intents = discord.Intents(members=True, guilds=True)
bot = MaaldarBot(intents=intents)

if __name__ == "__main__":
  pool.open(wait=False)
  bot.run(configuration["token"])
