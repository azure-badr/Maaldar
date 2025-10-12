from util import configuration, get_maaldar_user, insert_query, select_all

import discord

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
			if name.lower() in configuration["filtered_role_names"]:
				return await interaction.followup.send("Use a different role name 🙄")

			guild = interaction.guild

			role = await guild.create_role(name=name)
			await member.add_roles(role)

			insert_query(f"INSERT INTO Maaldar VALUES ('{member.id}', '{role.id}')")
			
			print(f"Role {role.name} {role.id} created and assigned to {member.name}")
			await interaction.followup.send(f"**{name}** created and assigned to you ✨")
			
			target_position = guild.get_role(configuration["custom_role_id"]).position - 1
			await role.edit(position=target_position)
			print(f"Role {role.name} {role.id} moved to position {target_position}")
			
			return

		role = interaction.guild.get_role(int(maaldar_user[1]))
		await interaction.followup.send(
			f"Your role already exists by the name `{role.name}`\n"
			"> Assign it to yourself by typing `/maaldar assign`\n"
			"> Want to change its name? Type `/maaldar name <new_name>`"
		)
	
	async def position(interaction: discord.Interaction):
		print("Positioning role for member", interaction.user.id)

		maaldar_user = interaction.extras["maaldar_user"]
		maaldar_user_role_id = int(maaldar_user[1])

		# Get Maaldar role ids
		maaldar_role_ids = select_all("SELECT role_id FROM Maaldar")
		maaldar_roles = [
			interaction.guild.get_role(int(role_data[0])) 
				for role_data in maaldar_role_ids
		]

		# Get Maaldar roles that the user has except their own
		user_maaldar_roles = [role for role in interaction.user.roles if role in maaldar_roles and not role.id == maaldar_user_role_id]
		print(f"Member [{interaction.user.id}] has {len(user_maaldar_roles)} other Maaldar roles (excluding their own Maaldar role)")
		if len(user_maaldar_roles) == 0:
			print(f"Member [{interaction.user.id}] has no Maaldar role to position their role around")
			await interaction.followup.send("You don't have any other Maaldar roles to position your role around! \nGet someone to give you a role first 😅")
			return
	
		if len(user_maaldar_roles) >= 25:
			print(f"Member [{interaction.user.id}] has too many Maaldar roles")
			await interaction.followup.send("You have way too many roles! 😱 - time to free up some space! \nType `/maaldar unassign` to get started")
			return

		view = DropdownPosition(user_maaldar_roles, maaldar_user_role_id, interaction.user.id)
		await interaction.followup.send("Select a role that you want to put your role above/below", view=view)


class DropdownPositionSelect(discord.ui.Select):
	def __init__(self, roles: list[discord.Role], user_maaldar_role_id: int, user_id: int):
		self.user_id = user_id
		self.user_maaldar_role_id = user_maaldar_role_id
		
		options = [
			discord.SelectOption(
				label=role.name,
				value=role.id
			) for role in roles
		]

		super().__init__(
			placeholder="Select a role",
			options=options
		)
	
	async def callback(self, interaction: discord.Interaction):
		if not interaction.user.id == self.user_id:
			await interaction.response.send_message("You didn't execute this command!", ephemeral=True)
			return
		
		role = interaction.guild.get_role(int(self.values[0]))
		custom_role = interaction.guild.get_role(int(configuration["custom_role_id"]))
		if role.position >= custom_role.position:
			await interaction.response.send_message(f"You can't move your role around **{role.name}** since it's above a risky permission role 😬.")
			return

		print(f"Member [{interaction.user.id}] attempting to position ther role around {role.name} [{role.id}]")

		view = DropdownAboveBelow(role, self.user_maaldar_role_id, self.user_id)
		await interaction.response.edit_message(content=f"Should your role be above or below **{role.name}**?", view=view)


class DropdownPosition(discord.ui.View):
  def __init__(self, *args):
    super().__init__()
    self.add_item(DropdownPositionSelect(*args))

class DropdownAboveBelowSelect(discord.ui.Select):
	def __init__(self, role: discord.Role, user_maaldar_role_id: int, user_id):
		self.user_id = user_id
		self.role = role
		self.user_maaldar_role_id = user_maaldar_role_id

		role_name = role.name if len(role.name) <= 25 else role.name[:25] + "..."
		options = [
			discord.SelectOption(
				label=f'{label} {role_name}',
				description=description,
				value=label
			) for label, description in [
					("Above", f"This will put your role one position above {role_name}"), 
					("Below", f"This will put your role one position below {role_name}")
				]
		]

		super().__init__(
			placeholder="Select a position",
			options=options
		)
	
	async def callback(self, interaction: discord.Interaction):
		if not interaction.user.id == self.user_id:
			await interaction.response.send_message("You didn't execute this command!", ephemeral=True)
			return

		await interaction.response.defer()
		role = interaction.guild.get_role(int(self.role.id))
		user_maaldar_role = interaction.guild.get_role(self.user_maaldar_role_id)

		print(f"Member [{interaction.user.id}] is positioning their role {self.values[0].lower()} {role.name} [{role.id}]")
		print(f"Member's [{interaction.user.id}] role position:", user_maaldar_role.position)
		print(f"Other role's position:", role.position)

		if self.values[0].lower() == "above":
			if user_maaldar_role.position == role.position + 1:
				print(f"Member's [{interaction.user.id}] role is already above the other role")
				await interaction.followup.send(f"Your role is already above **{role.name}**.")
				return
		
			await user_maaldar_role.edit(position=role.position)
		else:
			if user_maaldar_role.position == role.position - 1:
				print(f"Member's [{interaction.user.id}] role is already below the other role")
				await interaction.followup.send(f"Your role is already below **{role.name}**.")
				return

			await user_maaldar_role.edit(position=role.position - 1)
		
		await interaction.followup.send(f"Your role has been put {self.values[0].lower()} **{role.name}** ✨")
		await interaction.followup.send(
      "-# **Note**: Sometimes role positioning doesn't work since this server has many roles. If it didn't, ask Fauj to move it manually."
    )
		self.view.stop()

class DropdownAboveBelow(discord.ui.View):
	def __init__(self, *args):
		super().__init__()
		self.add_item(DropdownAboveBelowSelect(*args))


def setup(bot):
	bot.add_cog(Role(bot))
