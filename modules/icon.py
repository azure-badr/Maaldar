from util import get_maaldar_user, match_url_regex

import discord

import aiohttp

class Icon:
	async def icon(interaction: discord.Interaction, attachment: discord.Attachment = None, url: str = None) -> None:
		maaldar_user = get_maaldar_user(interaction.user.id)
		role: discord.Role = interaction.guild.get_role(int(maaldar_user[1]))

		if not url and not attachment:
			await role.edit(display_icon=None)
			await interaction.followup.send("Role icon removed 🗑️")
			return
		
		# If the attachment is provided, use that
		# NOTE: If the attachment and url are both provided, the attachment is given priority
		if attachment:
			try:
				if not attachment.content_type.startswith("image/"):
					await interaction.followup.send("The attachment must be an image! 🖼", ephemeral=True)
					return
				
				await role.edit(display_icon=await attachment.read())
				await interaction.followup.send("Role icon set ✨")
			except Exception as error:
				await interaction.followup.send(error)

			return

		if not match_url_regex(url):
			await interaction.followup.send("Enter a valid URL path!\n> It must end in .png or .jpg")
			return

		async with aiohttp.ClientSession() as session:
			async with session.get(url) as response:
				if not response.status == 200:
					await interaction.followup.send("Something is wrong with the website. Try a different one")
					return
				
				try:
					await role.edit(display_icon=await response.read())
					await interaction.followup.send("Role icon set ✨")
				except Exception as error:
					await interaction.followup.send(error)