from util import configuration, check_if_user_exists
from database.db import database

import discord

class Role:
	connection = database.connection
	cursor = database.cursor
	
	async def role(interaction: discord.Interaction, name: str) -> None:
		await interaction.response.defer()

		member = interaction.user
		maaldar_user = check_if_user_exists(member.id)
		if maaldar_user is None:
			guild = interaction.guild

			role = await guild.create_role(name=name)
			await role.edit(
				position=(guild.get_role(configuration["custom_role_id"]).position - 1)
			)
			await member.add_roles(role)

			Role.cursor.execute(
				f"INSERT INTO Maaldar VALUES ('{member.id}', '{role.id}')"
			)
			Role.connection.commit()

			await interaction.followup.send(f"**{name}** created and assigned to you ✨")
			return

		role = interaction.guild.get_role(int(maaldar_user[1]))
		await interaction.followup.send(
			f"Your role already exists by the name `{role.name}`\n"
			"> Assign it to yourself by typing `/maaldar assign`"
		)


def setup(bot):
	bot.add_cog(Role(bot))