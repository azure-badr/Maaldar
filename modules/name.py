from util import check_if_user_exists

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
		maaldar_user = check_if_user_exists(interaction.user.id)
		if maaldar_user is None:
			await interaction.followup.send(
				"You do not have a role yet.\n"
				"> Make one by typing `/maaldar role`"
			)
			return

		role = interaction.guild.get_role(int(maaldar_user[1]))
		await role.edit(name=new_name)
		await interaction.followup.send(f"Role name set to **{new_name}** ✨")