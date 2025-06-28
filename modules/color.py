import discord.http
from util import insert_query, select_one, insert_with_params, create_session_token, is_old_maaldar, set_maaldar_role_info, COLORS

import discord

import random

class Color:
  async def color(interaction: discord.Interaction, color: str = None, secondary_color: str = None) -> None:
    maaldar_user = interaction.extras["maaldar_user"]
    
    role = interaction.guild.get_role(int(maaldar_user[1]))

    if color is None and secondary_color:
      return await interaction.followup.send("To set a gradient, you need to set both the options for `color` and `secondary_color`")

    if color is None:
      set_maaldar_role_info(interaction.user.id, role.name, "0")
      await role.edit(color=discord.Color.default())
      
      await interaction.followup.send("Role color set to default")
      return

    if color == "holographic" or secondary_color:
      if len(role.members) > 1:
        return await interaction.followup.send("You cannot set a style for your role while it is assigned to other people 🙄\nSee who has your role with `/maaldar list`")
    
    print(f"[!] Setting color for {interaction.user.id}, params: {color}, {secondary_color}")
    if color == "holographic":
      messages = [
        "Maybe in another server, a holographic role could be a reality...",
        "A holographic role? In this server? Yeah, sure...",
        "😂 😂",
        "Role color set to holographic ✨.... In your dreams...",
        "Yeah, I'm working on it...",
        "HOLOGRAPHIC ROLE? ASK THE MODS WHAT HAPPENED TO THAT...",
        "We'll see about that..."
      ]
      return await interaction.followup.send(random.choice(messages))
    
      payload = { "colors": { "primary_color": 11127295, "secondary_color": 16759788, "tertiary_color": 16761760 } }
      await interaction.client.http.request(
        discord.http.Route(
          "PATCH",
          "/guilds/{guild_id}/roles/{role_id}",
          guild_id=interaction.guild.id,
          role_id=role.id
          ),
          json=payload,
        )
      await interaction.followup.send("Your role color is now holographic! 🌈")

      set_maaldar_role_info(interaction.user.id, role.name, payload)
      return

    color = color[1:].strip() if color.startswith("#") else color
    secondary_color = secondary_color[1:].strip() if secondary_color and secondary_color.startswith("#") else secondary_color
    try:
      color = int(color, 16)
      secondary_color = int(secondary_color, 16) if secondary_color else secondary_color
    except ValueError:
      await interaction.followup.send("Please enter the hex value for your color")
      return

    try:
      payload = { "colors": { "primary_color": color, "secondary_color": secondary_color }}
      await interaction.client.http.request(
        discord.http.Route(
          "PATCH",
          "/guilds/{guild_id}/roles/{role_id}",
          guild_id=interaction.guild.id,
          role_id=role.id
        ),
        json=payload,
      )
    except:
      await interaction.followup.send(
        "Please enter a valid hex value\n"
        "> Use Google color picker and copy the HEX value"
      )
      return

    await interaction.followup.send(f"New role color set ✨")
    set_maaldar_role_info(interaction.user.id, role.name, payload)


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
