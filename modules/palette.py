import discord
from discord.ext import commands, tasks

import asyncio

class Palette(commands.Cog):
    usage = 0
    cooldowns = []
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reset_usage.start()

    @staticmethod
    async def cooldown(author_id):
        Palette.usage += 1
        Palette.cooldowns.append(author_id)
        await asyncio.sleep(3600)
        Palette.cooldowns.remove(author_id)


    @tasks.loop(seconds=3500)
    async def reset_usage(self):
        Palette.usage = 0

    @reset_usage.before_loop
    async def before_reset_usage(self):
        await self.bot.wait_until_ready()

class Dropdown(discord.ui.Select):
  def __init__(self, *args):
    if len(args) == 4:
      self.role = args[2]
      self.user = args[3]
      options = [
        discord.SelectOption(
            label=f"{args[0][index]}", description=f"Color #{index + 1}", emoji=emoji
        ) for index, emoji in enumerate(args[1])
      ]
    else:
      self.role = args[1]
      self.user = args[2]
      options = [
        discord.SelectOption(
            label=f"#{args[0][index]}", description=f"Color #{index + 1}"
        ) for index in range(10)
      ]

    super().__init__(
      placeholder="Colors",
      min_values=1,
      max_values=1,
      options=options
    )

  async def callback(self, interaction: discord.Interaction):
    try:
      if interaction.user == self.user:
        await self.role.edit(
          color=discord.Color(
            int(self.values[0].strip('#'), 16)
          )
        )
        await interaction.response.send_message(
          f"Set your role color to `{self.values[0].upper()}` ✨"
        )
        await self.view.stop()

    except TypeError:
        pass


class DropdownViewPalette(discord.ui.View):
  def __init__(self, *args):
    super().__init__()
    self.add_item(Dropdown(*args))
