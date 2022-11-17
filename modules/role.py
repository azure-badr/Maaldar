from util import configuration, get_maaldar_user
from database.db import database

import discord

class Role:
	connection = database.connection
	cursor = database.cursor
	
	async def role(interaction: discord.Interaction, name: str) -> None:
		await interaction.response.defer()
		if len(interaction.guild.roles) >= 250:
			await interaction.followup.send(
				"> This server has reached the maximum number of roles 😱 - time to free up some space!"
			)
			return
		
		member = interaction.user
		maaldar_user = get_maaldar_user(member.id)
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
	
	async def position(interaction: discord.Interaction, below: str = None, above: str = None):
		if below is not None and above is not None:
			await interaction.response.send(
				"Please specify either `below` or `above`"
			)
			return
	
	async def position_below(interaction: discord.Interaction, below: str) -> list:
		pass		
	
	async def position_above(interaction: discord.Interaction, above: str) -> list:
		pass

def setup(bot):
	bot.add_cog(Role(bot))