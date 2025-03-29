from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
import discord

from modules.assignation import Assignation
from modules.palette import Palette
from modules.color import Color
from modules.role import Role
from modules.name import Name
from modules.icon import Icon

from util import get_maaldar_user, configuration, select_one

from psycopg2.errors import UndefinedFunction

import traceback

class Maaldar(commands.GroupCog, name="maaldar"):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
    self.delete_sessions.start()
  
  class NoCustomRole(app_commands.CheckFailure):
    pass

  def has_custom_role():
    async def predicate(interaction: discord.Interaction):
      if interaction.command.name == "color-picker":
        await interaction.response.defer(thinking=True, ephemeral=True)
      else:
        await interaction.response.defer()

      maaldar_user = get_maaldar_user(interaction.user.id)
      if maaldar_user is not None:
        interaction.extras["maaldar_user"] = maaldar_user
        return True

      error = "You do not have role yet! :desert:\nMake one by typing `/maaldar role`"
      raise Maaldar.NoCustomRole(error)
    
    return app_commands.check(predicate)

  # Role Command
  @app_commands.command(
    name="role", 
    description="Creates a new role for you"
  )
  @app_commands.describe(
    name="Name of the role you want to create"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  async def _role(self, interaction: discord.Interaction, name: str) -> None:
    await Role.role(interaction=interaction, name=name)

  # Name Command
  @app_commands.command(
    name="name",
    description="Sets a new name for your role"
  )
  @app_commands.describe(
    new_name="Name of the role"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  @has_custom_role()
  async def _name(self, interaction: discord.Interaction, new_name: str) -> None:
    await Name.name(interaction=interaction, new_name=new_name)

  # Color Command
  @app_commands.command(
    name="color", 
    description="Sets a new color for your role. Specifying no option resets your color"
  )
  @app_commands.describe(
    color="New color for your role (e.g #000000)"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  @has_custom_role()
  async def _color(self, interaction: discord.Interaction, color: str = None) -> None:
    await Color.color(interaction=interaction, color=color)

  # Icon Command
  @app_commands.command(
    name="icon", 
    description="Sets an icon for your role. If the url and attachment are not provided, it removes the icon"
  )
  @app_commands.describe(
    attachment="Image to be used as the icon",
    url="URL link to the icon (must be in PNG/JPG format)"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  @has_custom_role()
  async def _icon(self, interaction: discord.Interaction, attachment: discord.Attachment = None, url: str = None) -> None:
    await Icon.icon(interaction=interaction, attachment=attachment, url=url)
  
  # Assign Command
  @app_commands.command(
    name="assign", 
    description="Assigns your role to you"
  )
  @app_commands.describe(
    user="User to assign the role to"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  @has_custom_role()
  async def _assign(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
    await Assignation.assign(interaction=interaction, user=user)
  
  # Unassign Command
  @app_commands.command(
    name="unassign", 
    description="Unassigns your role from you"
  )
  @app_commands.describe(
    user="User to unassign the role from"
  )
  @app_commands.describe(
    role="Maaldar Role to unassign from yourself"
  )
  async def _unassign(self, interaction: discord.Interaction, user: discord.Member = None, role: discord.Role = None) -> None:
    await Assignation.unassign(interaction=interaction, user=user, role=role)

  "Palette Command"
  @app_commands.command(
    name="palette",
    description="Gets a color palette for your profile picture"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  @has_custom_role()
  async def _palette(self, interaction: discord.Interaction) -> None:
    await Palette.palette(interaction=interaction)

  "Color Picker Command"
  @app_commands.command(
    name="color-picker",
    description="Pick a color for your role from a colour picker. (Must have DMs enabled)"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  @has_custom_role()
  async def _color_picker(self, interaction: discord.Interaction) -> None:
    await Color.color_picker(interaction=interaction)
  
  @app_commands.command(
    name="position",
    description="Positions your role to other Maaldar roles"
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  @has_custom_role()
  async def _position(self, interaction: discord.Interaction) -> None:
    await Role.position(interaction=interaction)
  
  @_name.error
  @_role.error
  @_color.error
  @_icon.error
  @_assign.error
  @_unassign.error
  @_color_picker.error
  @_palette.error
  @_position.error
  async def commands_error(self, interaction: discord.Interaction, error: commands.CommandError) -> None:
    print(f"[!] {interaction.user} used {interaction.command.name} command in {interaction.channel.name} and got an error:")

    if not interaction.response.is_done():
      await interaction.response.defer()
    
    if isinstance(error, Maaldar.NoCustomRole):
      await interaction.followup.send(error)
      return

    if isinstance(error, discord.app_commands.errors.MissingAnyRole):
      await interaction.followup.send(
        "You need to be boosting the server to use this command 🪙", 
        ephemeral=True
      )
      return
    
    print("".join(traceback.format_exception(type(error), error, error.__traceback__)))
    await interaction.followup.send("Sorry, something went wrong... :desert:", ephemeral=True)

    # Send a DM to the owner of the bot about the error
    guild = interaction.guild
    member = guild.get_member(configuration["owner_id"])

    await member.send(
      f"[!] {interaction.user} used {interaction.command.name} command in {interaction.channel.name} and got an error:\n {error}",
    )
  
  @tasks.loop(seconds=3600)
  async def delete_sessions(self):
    print("Deleting expired sessions for color-picker...")
    try:
      select_one("SELECT delete_expired_sessions();")
    except UndefinedFunction as error:
      print("[!] delete_expired_sessions() function does not exist on your database.")
      print("[!] Run maaldar-db/maaldar_session.sql on your database.")
      print(error)
  
  @delete_sessions.before_loop
  async def before_delete_sessions(self):
    await self.bot.wait_until_ready()
  
async def setup(bot: commands.Bot):
  await bot.add_cog(Maaldar(bot), guilds=[discord.Object(id=configuration["guild_id"])])