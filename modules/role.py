from util import configuration, get_maaldar_user
from database.db import database

import discord
from discord import app_commands

class Role:
	connection = database.connection
	cursor = database.cursor
	
	async def role(interaction: discord.Interaction, name: str) -> None:
		await interaction.response.defer()

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
	
	async def position(interaction: discord.Interaction, role_name: str, above: bool):
		maaldar_user = get_maaldar_user(interaction.user.id)
		maaldar_user_role_id = maaldar_user[1]
		role_id = role_name # role_name gets converted to role_id by the autocomplete function
		
		if maaldar_user_role_id == role_id:
			await interaction.response.send_message("You can't move relative to your own role 🤦")
			return
		
		role = interaction.guild.get_role(int(role_id))
		custom_role = interaction.guild.get_role(int(configuration["custom_role_id"]))
		if role.position >= custom_role.position:
			await interaction.response.send_message("You can't move your role up there *(for obvious reasons)* 🤫")
			return
		
		maaldar_user_role = interaction.guild.get_role(int(maaldar_user_role_id))
		if above and maaldar_user_role.position == role.position + 1:
			await interaction.response.send_message("Your role is already above that role 🤷")
			return
		
		if not above and maaldar_user_role.position == role.position - 1:
			await interaction.response.send_message("Your role is already below that role 🤷")
			return

		if above:
			if maaldar_user_role.position > role.position:
				await maaldar_user_role.edit(position=role.position + 1)
				return await interaction.response.send_message(f"Moved your role above {role.name} ✨")
			
			await maaldar_user_role.edit(position=role.position)
			return await interaction.response.send_message(f"Moved your role above {role.name} ✨")
		
		if maaldar_user_role.position < role.position:
			await maaldar_user_role.edit(position=role.position - 1)
			return await interaction.response.send_message(f"Moved your role below {role.name} ✨")
		
		await maaldar_user_role.edit(position=role.position)
		return await interaction.response.send_message(f"Moved your role below {role.name} ✨")
		
	async def position_autocomplete(self, interaction: discord.Interaction, role_name: str) -> list[app_commands.Choice[str]]:
		Role.cursor.execute("SELECT role_id FROM Maaldar")
		maaldar_role_ids = Role.cursor.fetchall()
		
		roles = []
		if not role_name == "":
			roles = [role for role in roles if role.name.startswith(role_name)]
		else:
			roles = [interaction.guild.get_role(int(role_id[0])) for role_id in maaldar_role_ids]

		return [app_commands.Choice(name=role.name, value=str(role.id)) for role in roles[:25]]

def setup(bot):
	bot.add_cog(Role(bot))