import discord.http
from util import insert_query, select_one, create_session_token, COLORS

import discord

class Color:
  async def color(interaction: discord.Interaction, color: str = None, secondary_color: str = None) -> None:
    maaldar_user = interaction.extras["maaldar_user"]
    
    role = interaction.guild.get_role(int(maaldar_user[1]))
    if color is None:
      await role.edit(color=discord.Color.default())
      
      await interaction.followup.send("Role color set to default")
      return
    
    if color == "holographic":
      await interaction.client.http.request(
        discord.http.Route(
          "PATCH",
          "/guilds/{guild_id}/roles/{role_id}",
          guild_id=interaction.guild.id,
          role_id=role.id
          ),
          json={ 
            "colors": {
              "primary_color": 11127295,
              "secondary_color": 16759788,
              "tertiary_color": 16761760
            } 
          },
        )
      
      await interaction.followup.send("Your role color is now holographic! 🌈")
      return

    color = color[1:] if color.startswith("#") else color
    secondary_color = secondary_color[1:] if secondary_color and secondary_color.startswith("#") else secondary_color
    try:
      color = int(color, 16)
      secondary_color = int(secondary_color, 16) if secondary_color else secondary_color
    except ValueError:
      await interaction.followup.send("Please enter the hex value for your color")
      return

    try:
      if secondary_color:
        await interaction.client.http.request(
          discord.http.Route(
            "PATCH",
            "/guilds/{guild_id}/roles/{role_id}",
            guild_id=interaction.guild.id,
            role_id=role.id
          ),
          json={ 
            "colors": {
              "primary_color": color,
              "secondary_color": secondary_color,
            } 
          },
        )
      else:
        await role.edit(color=discord.Color(color))
    except:
      await interaction.followup.send(
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
