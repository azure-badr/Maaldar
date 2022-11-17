from discord.ext import commands
from discord import app_commands
import discord

from modules.assignation import Assignation
from modules.palette import Palette
from modules.color import Color
from modules.role import Role
from modules.name import Name
from modules.icon import Icon

from database.db import database
from util import get_maaldar_user, configuration

class Maaldar(commands.GroupCog, name="maaldar"):
  connection = database.connection
  cursor = database.cursor
  
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
  
  class NoCustomRole(app_commands.CheckFailure):
    pass

  def has_custom_role():
    async def predicate(interaction: discord.Interaction):
      maaldar_user = get_maaldar_user(interaction.user.id)
      if maaldar_user is not None:
        return True

      error = "You do not have role yet! :desert:"
      if not interaction.command.name == "unassign":
        error += "\nMake one by typing `/maaldar role`"
      
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
  @has_custom_role()
  async def _unassign(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
    await Assignation.unassign(interaction=interaction, user=user)

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
    description="Positions your role relative to other roles"
  )
  @app_commands.autocomplete(
    above=Role.position_above, 
    below=Role.position_below
  )
  @app_commands.checks.has_any_role(*configuration["role_ids"])
  async def _position(self, interaction: discord.Interaction, below: str = None, above: str = None) -> None:
    await Role.position(interaction=interaction, below=below, above=above)
  
  @_name.error
  @_role.error
  @_color.error
  @_icon.error
  @_assign.error
  @_unassign.error
  @_color_picker.error
  @_palette.error
  async def commands_error(self, interaction: discord.Interaction, error: commands.CommandError) -> None:
    print(error)
    
    await interaction.response.send_message("Sorry, something wrong... :desert:", ephemeral=True)
    if isinstance(error, Maaldar.NoCustomRole):
      await interaction.response.send_message(error)
      return

    if isinstance(error, discord.app_commands.errors.MissingAnyRole):
      await interaction.response.send_message(
        "You need to be boosting the server to use this command 🪙", 
        ephemeral=True
      )
      return

async def setup(bot: commands.Bot):
  await bot.add_cog(Maaldar(bot), guilds=[discord.Object(id=configuration["guild_id"])])