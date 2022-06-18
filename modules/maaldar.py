import asyncio
import io
import sqlite3

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks
from modules.palette import DropdownViewPalette, Palette
from modules.color import Color

from colorthief import ColorThief

from util import DropdownView, clean_up, concatenate_images, configuration, check_if_user_exists, make_image, match_url_regex, rgb_to_hex

@app_commands.guild_only()
class Maaldar(commands.Cog):
  connection = sqlite3.connect("maaldar.db")
  cursor = connection.cursor()
  
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
    self.palette = Palette(self.bot)

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
    new_name="Name of the role"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def name(self, interaction: discord.Interaction, new_name: str) -> None:
    if len(new_name) > 100:
      await interaction.followup.send(
        "🤔 I wouldn't do that\n"
        "> Role name must be fewer than 100 characters"
      )
      return

    await interaction.response.defer()
    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
      await interaction.followup.send(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return

    role = interaction.guild.get_role(int(maaldar_user[1]))
    await role.edit(name=new_name)
    await interaction.followup.send(f"Role name set to **{new_name}** ✨")

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
    
    color = color[1:] if color.startswith("#") else color
    try:
      color = int(color, 16)
    except ValueError:
      await interaction.followup.send("Please enter the hex value for your color")
      return

    role = interaction.guild.get_role(int(maaldar_user[1]))
    try:
      await role.edit(color=discord.Color(color))
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
        await interaction.followup.send(
          "You do not have a role yet.\n"
          "> Make one by typing `/maaldar create`"
        )
        return

    role: discord.Role = interaction.guild.get_role(int(maaldar_user[1]))

    if not url:
      await role.edit(display_icon=None)
      await interaction.followup.send("Role icon removed 🗑️")
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
    await interaction.response.defer()
    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
      await interaction.followup.send(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return
    
    role = interaction.guild.get_role(int(maaldar_user[1]))
    if not user:
      await interaction.user.add_roles(role)
      await interaction.followup.send(f"Role assigned to you ✨")

      return
    
    view = DropdownView(user, role)
    await interaction.followup.send(
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
  async def unassign(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
    await interaction.response.defer()
    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
      await interaction.followup.send(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return
    
    role = interaction.guild.get_role(int(maaldar_user[1]))
    if not user:
      await interaction.user.remove_roles(role)
      await interaction.followup.send(f"Role unassigned from you")

      return
    
    await user.remove_roles(role)
    await interaction.followup.send(f"Role unassigned from **{user.name}**")

  "Palette Command"
  @maaldar_group.command(
    name="palette",
    description="Gets a color palette for your profile picture"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def palette(self, interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    maaldar_user = check_if_user_exists(Maaldar.cursor, interaction.user.id)
    if maaldar_user is None:
      await interaction.followup.send(
        "You do not have a role yet.\n"
        "> Make one by typing `/maaldar create`"
      )
      return
    
    """Cooldown check"""
    user_reattempt = interaction.user.id in self.palette.cooldowns

    """Launch a cooldown on the command executing user"""
    asyncio.ensure_future(self.palette.cooldown(interaction.user.id))


    """Read profile picture from avatar.url"""
    buffer: io.BytesIO
    async with aiohttp.ClientSession() as session:
      async with session.get(interaction.user.avatar.url) as response:
        if response.status == 200:
          buffer = io.BytesIO(await response.read())

    """Get color palette and make new images with them"""
    color_palette = ColorThief(
        buffer
    ).get_palette(color_count=11)

    hex_values = []
    images = []
    for dominant_color in color_palette:
        hex_values.append(rgb_to_hex(dominant_color))

        image = make_image(dominant_color)
        images.append(image)

    role = interaction.guild.get_role(int(maaldar_user[1]))
    """
    If usage is greater than 5 then use traditional method instead
    of role uploading
    """
    if self.palette.usage > 5 or user_reattempt:
      concatenate_images(images)
      await interaction.followup.send(
        file=discord.File("./palette.png")
      )
      clean_up()

      view = DropdownViewPalette(hex_values, role, interaction.user)
      await interaction.followup.send("Choose the color you want", view=view)
      return
    
    """Convert the images to file-like objects"""
    emojis = []
    for image in images:
      image_byte_array = io.BytesIO()
      image.save(image_byte_array, "PNG")
      emojis.append(
          image_byte_array.getvalue())

    """Add the emojis to the guild"""
    emojis_guild: discord.Guild = interaction.client.get_guild(
        configuration["emoji_server_id"]
    )
    added_emojis = []

    for index, emoji in enumerate(emojis, start=0):
      added_emojis.append(
        await emojis_guild.create_custom_emoji(
          name=hex_values[index], 
          image=emoji
        )
      )

    view = DropdownViewPalette(hex_values, added_emojis, role, interaction.user)
    await interaction.followup.send(
      "Choose the color you want",
      view=view
    )
    for emoji in added_emojis:
      await emojis_guild.delete_emoji(emoji)

  "Color Picker Command"
  @maaldar_group.command(
    name="color-picker",
    description="Pick a color for your role from a colour picker. (Must have DMs enabled)"
  )
  @app_commands.checks.has_any_role(
    *configuration["role_ids"]
  )
  async def color_picker(self, interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    Color.cursor.execute(
        "SELECT * FROM MaaldarSession WHERE user_id = ?", (interaction.user.id, )
    )
    maaldar_session = Color.cursor.fetchone()
    if not maaldar_session:
        asyncio.ensure_future(Color.create_session(interaction))
        return

    await interaction.followup.send(f"Session already exists\n> Please check your DM")
    return
  

  @name.error
  @role.error
  @color.error
  @icon.error
  @assign.error
  @unassign.error
  @color_picker.error
  async def commands_error(self, interaction: discord.Interaction, error: commands.CommandError) -> None:
    if (isinstance(error, discord.app_commands.errors.MissingAnyRole)):
      await interaction.response.send_message(
        "You need to be boosting the server to use this command", 
        ephemeral=True
      )
      return
    
    print(error)
  
  @tasks.loop(seconds=3600)
  async def reset_usage(self):
    Maaldar.usage = 0

async def setup(bot: commands.Bot):
  await bot.add_cog(Maaldar(bot), guilds=[discord.Object(id=configuration["guild_id"])])
