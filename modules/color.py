from util import get_maaldar_user, delete_query, insert_query, select_one

import discord

import uuid
import asyncio

class Color:
  async def color(interaction: discord.Interaction, color: str = None) -> None:
    await interaction.response.defer()
    
    maaldar_user = get_maaldar_user(interaction.user.id)
    
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

  async def color_picker(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    maaldar_session = select_one(f"SELECT * FROM MaaldarSession WHERE user_id = '{interaction.user.id}'")
    if not maaldar_session:
      await asyncio.create_task(Color.create_session(interaction))
      return

    await interaction.followup.send(f"Session already exists\n> Please check your DM")
    return

  @staticmethod
  async def create_session(interaction):
    session = uuid.uuid4().hex
    insert_query(f"INSERT INTO MaaldarSession (user_id, token) VALUES ('{interaction.user.id}', '{session}')")
    await interaction.followup.send("Created session, please check your DM")

    try:
      await interaction.user.send(
        "Session created ✨\n"
        f"> https://pakcord-color-picker.fly.dev/{session}"
      )
      """Wait for 1 hour and delete session"""
      await asyncio.sleep(3600)
      delete_query(f"DELETE FROM MaaldarSession WHERE user_id = '{interaction.user.id}'"
)

    except discord.Forbidden:
      await interaction.followup.send("Please enable your DMs")
      delete_query(f"DELETE FROM MaaldarSession WHERE user_id = '{interaction.user.id}'")