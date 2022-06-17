import discord
from discord import app_commands
from discord.ext import commands

from util import configuration

class MaaldarBot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix='', intents=intents)
    
    async def on_ready(self) -> None:
      await self.wait_until_ready()
      await self.tree.sync(guild=discord.Object(id=configuration["guild_id"]))

    async def setup_hook(self) -> None:
      await self.load_extension("modules.maaldar")

intents = discord.Intents(members=True, guilds=True)
bot = MaaldarBot(intents=intents)

if __name__ == "__main__":
  bot.run(configuration["token"])
