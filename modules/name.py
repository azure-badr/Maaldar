from util import get_maaldar_user

import discord

class Name:
	async def name(interaction: discord.Interaction, new_name: str) -> None:
		if len(new_name) > 100:
			await interaction.followup.send(
        "🤔 I wouldn't do that\n"
        "> Role name must be fewer than 100 characters"
      )
			return

		await interaction.response.defer()
		maaldar_user = get_maaldar_user(interaction.user.id)
		role = interaction.guild.get_role(int(maaldar_user[1]))
		await role.edit(name=new_name)
		await interaction.followup.send(f"Role name set to **{new_name}** ✨")