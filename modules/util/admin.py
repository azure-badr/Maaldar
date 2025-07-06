from discord.ext import commands
from discord import app_commands
import discord

import datetime

from util import configuration, select_one

class Administration(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot
  
  @app_commands.command(
    name="info",
    description="Provides information about a target"
  )
  @app_commands.describe(
    user="Information about user",
  )
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def info(self, interaction: discord.Interaction, user: discord.Member) -> None:
    maaldar_info = select_one(
      "SELECT Maaldar.role_id, MaaldarDuration.boosting_since "
      "FROM Maaldar "
      "JOIN MaaldarRoles ON Maaldar.user_id = MaaldarRoles.user_id "
      "LEFT JOIN MaaldarDuration ON Maaldar.user_id = MaaldarDuration.user_id "
      f"WHERE Maaldar.user_id = '{user.id}'"
    )

    if maaldar_info is None:
      return await interaction.response.send_message("This user is not a Maaldar user")
    
    role_id, boosting_since = maaldar_info
    if role_id:
      role = interaction.guild.get_role(int(role_id))
    
    message = f"**Role ID:** {role.id}\n**Role name:** {role.name}"
    if boosting_since:
      message +=  f"\n**Boosting since:** {Administration._format_seconds(boosting_since)}"

    await interaction.response.send_message(message)
  
  @staticmethod
  def _format_seconds(seconds):
    if seconds is None:
      return "Not boosting"

    delta = datetime.timedelta(seconds=seconds)
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days:
      parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
      parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
      parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    return ", ".join(parts) or "Less than a minute"


async def setup(bot: commands.Bot):
  await bot.add_cog(Administration(bot), guilds=[discord.Object(id=configuration["guild_id"])])
