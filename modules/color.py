from util import insert_query, select_one, create_session_token, COLORS

import discord
from discord.ext import tasks

class Color:
  async def color(interaction: discord.Interaction, color: str = None) -> None:
    maaldar_user = interaction.extras["maaldar_user"]
    
    if color is None:
      role = interaction.guild.get_role(int(maaldar_user[1]))
      await role.edit(color=discord.Color.default())
      
      await interaction.followup.send("Role color set to default")
      return
    
    # FIX: color = COLORS.get(color.lower(), color)

    color = color[1:] if color.startswith("#") else color
    try:
      if color == "random":
        color = discord.Color.random().value
      else:
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
    maaldar_session = select_one(f"SELECT * FROM MaaldarSession WHERE user_id = '{interaction.user.id}'")
    if not maaldar_session:
      session = create_session_token()
      
      insert_query(f"INSERT INTO MaaldarSession (user_id, token) VALUES ('{interaction.user.id}', '{session}')")
      await interaction.followup.send(
        "You can now change your color at\n"
        f"> https://maaldar.pakcord.me/{session} ✨"
      )
      return
    
    await interaction.followup.send(
      "You can change your color at\n"
      f"> https://maaldar.pakcord.me/{maaldar_session[1]} ✨"
    )
