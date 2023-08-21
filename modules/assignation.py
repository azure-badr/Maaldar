from util import get_maaldar_user, select_one

import discord

class Assignation:
	async def assign(interaction: discord.Interaction, user: discord.Member = None) -> None:
		maaldar_user = get_maaldar_user(interaction.user.id)
		role = interaction.guild.get_role(int(maaldar_user[1]))
		if not user:
			await interaction.user.add_roles(role)
			await interaction.followup.send(f"Role assigned to you ✨")

			return
		
		view = DropdownView(user, role)
		await interaction.followup.send(
			f"{user.mention}, {interaction.user.name} is trying to assign you their role", 
			view=view
		)

	async def unassign(interaction: discord.Interaction, user: discord.Member = None, role: discord.Role = None) -> None:
		if user and role:
			return await interaction.followup.send("You can't specify both a user and a role, chief.", ephemeral=True)
		
		# If no user or role is specified, unassign the user's own role from themselves
		if not user and not role:
			maaldar_user = get_maaldar_user(interaction.user.id)
			role = interaction.guild.get_role(int(maaldar_user[1]))
			
			await interaction.user.remove_roles(role)
			await interaction.followup.send(f"Role unassigned from you")

			return
		

		# If a role is specified, verify if it's a Maaldar role and unassign it from the user
		if role:
			is_maaldar_role = select_one(f"SELECT * FROM Maaldar WHERE role_id = '{role.id}'")
			if not is_maaldar_role:
				return await interaction.followup.send("You can only unassign a Maaldar role from yourself", ephemeral=True)
			
			if not role in interaction.user.roles:
				return await interaction.followup.send("You don't have that role 🧐", ephemeral=True)
			
			await interaction.user.remove_roles(role)
			return await interaction.followup.send(f"Role unassigned from you", ephemeral=True)

		# If a user is specified, remove your role from them
		maaldar_user = get_maaldar_user(interaction.user.id)
		role = interaction.guild.get_role(int(maaldar_user[1]))
		
		await user.remove_roles(role)
		await interaction.followup.send(f"Role unassigned from **{user.name}**")


class Dropdown(discord.ui.Select):
	def __init__(self, assignee, role):
		self.assignee = assignee
		self.role = role

		options = [
			discord.SelectOption(
				label="Yes", description="I want the role (I love them)", emoji='✅'
			),
			discord.SelectOption(
				label="No", description="I do not want the role (I hate them)", emoji='❎'
			)
		]

		super().__init__(
			placeholder="Choose whether you'd like the role",
			min_values=1,
			max_values=1,
			options=options
		)

	async def callback(self, interaction: discord.Interaction):
		if not interaction.user == self.assignee:
			await interaction.response.send_message("You're not the one they're giving the role to, chief.", ephemeral=True)
			return

		if self.values[0] == "Yes":
			await self.assignee.add_roles(self.role)
			await interaction.response.send_message("The role has been assigned to you ✨")
		
		if self.values[0] == "No":
			await interaction.response.send_message("They won't know you did that. Keep it a secret 🤫", ephemeral=True)

		self.view.stop()


class DropdownView(discord.ui.View):
	def __init__(self, assignee, role):
		super().__init__()
		self.add_item(Dropdown(assignee, role))