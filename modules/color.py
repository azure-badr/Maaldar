from database.db import database
from util import get_maaldar_user

import discord

import uuid
import asyncio

class Color:
  connection = database.connection
  cursor = database.cursor

  def __init__(self):
    # Clear the MaaldarSession table on startup
    Color.cursor.execute("SELECT * FROM MaaldarSession")
    maaldar_sessions = Color.cursor.fetchall()
    print(maaldar_sessions)
    print("[!] Clearing MaaldarSession")
    
    Color.cursor.execute("DELETE FROM MaaldarSession")
    Color.connection.commit()

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
    Color.cursor.execute(
      f"SELECT * FROM MaaldarSession WHERE user_id = '{interaction.user.id}'"
    )
    maaldar_session = Color.cursor.fetchone()
    if not maaldar_session:
        asyncio.ensure_future(Color.create_session(interaction))
        return

    await interaction.followup.send(f"Session already exists\n> Please check your DM")
    return

  @staticmethod
  async def create_session(interaction):
    session = uuid.uuid4().hex
    Color.cursor.execute(
      f"INSERT INTO MaaldarSession VALUES ('{interaction.user.id}', '{session}')"
    )
    Color.connection.commit()
    await interaction.followup.send("Created session, please check your DM")

    try:
      await interaction.user.send(
        "Session created ✨\n"
        f"> https://pakcord-color-picker.fly.dev/{session}"
      )
      """Wait for 1 hour and delete session"""
      await asyncio.sleep(3600)
      Color.cursor.execute(
        f"DELETE FROM MaaldarSession WHERE user_id = '{interaction.user.id}'"
      )
      Color.connection.commit()

    except discord.Forbidden:
      await interaction.followup.send("Please enable your DMs")
      Color.cursor.execute(
        "DELETE FROM MaaldarSession WHERE user_id = '{interaction.user.id}'"
      )
      Color.connection.commit()