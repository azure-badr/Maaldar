from util import configuration, get_maaldar_user, insert_query, select_all

import discord
from discord import app_commands

class Role:
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

			insert_query(f"INSERT INTO Maaldar VALUES ('{member.id}', '{role.id}')")

			await interaction.followup.send(f"**{name}** created and assigned to you ✨")
			return

		role = interaction.guild.get_role(int(maaldar_user[1]))
		await interaction.followup.send(
			f"Your role already exists by the name `{role.name}`\n"
			"> Assign it to yourself by typing `/maaldar assign`\n"
			"> Want to change its name? Type `/maaldar name <new_name>`"
		)
	
	async def position(interaction: discord.Interaction, role_name: str, above: bool):
		maaldar_user = get_maaldar_user(interaction.user.id)
		maaldar_user_role_id = maaldar_user[1]
		role_id = role_name # role_name gets converted to role_id by the autocomplete function
		
		if maaldar_user_role_id == role_id:
			await interaction.response.send_message("You can't move relative to your own role! Put it above or below another role")
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
		await interaction.response.defer()
		maaldar_role_ids = select_all("SELECT role_id FROM Maaldar")
		

		roles = [interaction.guild.get_role(int(role_id[0])) for role_id in maaldar_role_ids]
		if not role_name == "":
			roles = [role for role in roles if role.name.startswith(role_name)]
			
		return [app_commands.Choice(name=role.name, value=str(role.id)) for role in roles[:25]]

def setup(bot):
	bot.add_cog(Role(bot))