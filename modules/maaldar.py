import sqlite3

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from util import DropdownView, configuration, check_if_user_exists, match_url_regex

@app_commands.guild_only()
class Maaldar(commands.Cog):
  connection = sqlite3.connect("maaldar.db")
  cursor = connection.cursor()
  
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot

  maaldar_group = app_commands.Group(name="maaldar", description="Maaldar commands")

  """ Role Command """
  @maaldar_group.command(
    name="role", 
    description="Creates a new role for you"
  )
  @app_commands.describe(
    name="Name of the role you want to create"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def role(self, interaction: discord.Interaction, name: str) -> None:
    await interaction.response.defer()

    member = interaction.user
    maaldar_user = check_if_user_exists(Maaldar.cursor, member.id)
    if maaldar_user is None:
      try:
        guild = interaction.guild

        role = await guild.create_role(name=name)
        await role.edit(
          position=(guild.get_role(configuration["custom_role_id"]).position - 1)
        )
        await member.add_roles(role)

        Maaldar.cursor.execute(
            "INSERT INTO Maaldar VALUES (?, ?)", (member.id, role.id)
        )
        Maaldar.connection.commit()

        await interaction.followup.send(f"**{name}** created and assigned to you ✨")
        return
      except Exception as error:
        print(error)

    role = interaction.guild.get_role(int(maaldar_user[1]))
    await interaction.followup.send(
      f"Your role already exists by the name `{role.name}`\n"
      "> Assign it to yourself by typing `/maaldar assign`"
    )
  
  """Name Command"""
  @maaldar_group.command(
    name="name", 
    description="Sets a new name for your role"
  )
  @app_commands.describe(
    name="Name of the role"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def name(self, interaction: discord.Interaction, name: str) -> None:
    if len(name) > 100:
      await interaction.response.send(
        "🤔 I wouldn't do that\n"
        "> Role name must be fewer than 100 characters"
      )
      return

    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user)
    if maaldar_user is None:
      await interaction.response.send(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return

    role = interaction.guild.get_role(int(maaldar_user[1]))
    await role.edit(name=name)
    await interaction.response.send(f"Role name set to **{name}** ✨")

  """Color Command"""
  @maaldar_group.command(
    name="color", 
    description="Sets a new color for your role. Specifying no option resets your color"
  )
  @app_commands.describe(
    color="New color for your role (e.g #000000)"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def color(self, interaction: discord.Interaction, color: str = None) -> None:
    await interaction.response.defer()

    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
      await interaction.response.send(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return

    if color is None:
      role = interaction.guild.get_role(int(maaldar_user[1]))
      await role.edit(color=discord.Color.default())
      
      await interaction.followup.send("Role color set to default")
      return
    
    color = color[1:] if color.startswith("#") else new_color
    try:
      new_color = int(new_color, 16)
    except ValueError:
      await interaction.followup.send("Please enter the hex value for your color")
      return

    role = interaction.guild.get_role(int(maaldar_user[1]))
    try:
      await role.edit(color=discord.Color(new_color))
    except:
      await interaction.response.send(
        "Please enter a valid hex value\n"
        "> Use Google color picker and copy the HEX value"
      )
      return

    await interaction.followup.send(f"New role color set ✨")

  """Icon Command"""
  @maaldar_group.command(
    name="icon", 
    description="Sets an icon for your role. If the url is not provided, it removes the icon"
  )
  @app_commands.describe(
    url="URL link to the icon (must be in PNG/JPG format)"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def icon(self, interaction: discord.Interaction, url: str = None) -> None:
    await interaction.response.defer()
    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
        await interaction.followup.respond(
          "You do not have a role yet.\n"
          "> Make one by typing `/maaldar create`"
        )
        return

    role: discord.Role = interaction.guild.get_role(int(maaldar_user[1]))

    if not url:
      await role.edit(icon=None)
      await interaction.followup.respond("Role icon removed 🗑️")
      return

    if not match_url_regex(url):
      await interaction.followup.send("Enter a valid URL path!\n> It must end in .png or .jpg")
      return

    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        if response.status == 200:
          try:
            await role.edit(display_icon=await response.read())
            await interaction.followup.send("Role icon set ✨")
            return

          except Exception as error:
            await interaction.followup.send(error)
            return

        await interaction.followup.send("Something is wrong with the website. Try a different one 👉")
  
  "Assignation Command"
  @maaldar_group.command(
    name="assign", 
    description="Assigns your role to you"
  )
  @app_commands.describe(
    user="User to assign the role to"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def assign(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
      await interaction.response.send_message(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return
    
    role = interaction.guild.get_role(int(maaldar_user[1]))
    if user is None:
      await interaction.user.add_roles(role)
      await interaction.response.send(f"Role assigned to you ✨")

      return
    
    view = DropdownView(user, role)
    await interaction.response.send_message(
      f"{user.mention}, {interaction.user.name} is trying to assign you their role", 
      view=view
    )
  
  "Unassign Command"
  @maaldar_group.command(
    name="unassign", 
    description="Unassigns your role from you"
  )
  @app_commands.describe(
    user="User to unassign the role from"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def assign(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
      await interaction.response.send_message(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return
    
    role = interaction.guild.get_role(int(maaldar_user[1]))
    if user is None:
      await interaction.user.remove_roles(role)
      await interaction.response.send_message(f"Role unassigned from you")

      return
    
    await user.remove_roles(role)
    await interaction.response.send_message(f"Role unassigned from **{user.name}**")

  @name.error
  @role.error
  @color.error
  @icon.error
  @assign.error
  async def commands_error(self, interaction: discord.Interaction, error: commands.CommandError) -> None:
    if (isinstance(error, commands.MissingAnyRole)):
      await interaction.response.send_message(
        "You need to be boosting the server to use this command", 
        ephemeral=True
      )

async def setup(bot: commands.Bot):
  await bot.add_cog(Maaldar(bot), guilds=[discord.Object(id=configuration["guild_id"])])