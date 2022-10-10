from util import get_maaldar_user

import discord

class Assignation:
	async def assign(interaction: discord.Interaction, user: discord.Member = None) -> None:
		await interaction.response.defer()
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

	async def unassign(interaction: discord.Interaction, user: discord.Member = None) -> None:
		await interaction.response.defer()
		maaldar_user = get_maaldar_user(interaction.user.id)
		role = interaction.guild.get_role(int(maaldar_user[1]))
		if not user:
			await interaction.user.remove_roles(role)
			await interaction.followup.send(f"Role unassigned from you")

			return
		
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