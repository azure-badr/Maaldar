import discord
from discord.ext import commands
from discord.commands import permissions, Option

from util import configuration, check_if_user_exists
from main import maaldar

import sqlite3


class Assignation(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    def __init__(self, bot):
        self.bot = bot

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def assign(ctx, assignee: Option(discord.Member, "Assigns your role to someone", required=False) = None):
        """Assigns your role to you"""

        maaldar_user = check_if_user_exists(Assignation.cursor, ctx.author.id)
        if maaldar_user is None:
            await ctx.respond("You do not have a role yet.\n"
                              "> Make one by typing `/maaldar create`")
            return

        role = ctx.guild.get_role(int(maaldar_user[1]))
        if not assignee:
            await ctx.author.add_roles(role)
            await ctx.respond(f"Role assigned to you ✨")
            return

        view = DropdownView(assignee, role)
        await ctx.respond(f"{assignee.mention}, {ctx.author.name} is trying to assign you their role", view=view)

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def unassign(ctx, assignee: Option(discord.Member, "Unassigns your role from someone", required=False) = None):
        """Unassigns your role from you"""

        maaldar_user = check_if_user_exists(Assignation.cursor, ctx.author.id)
        if maaldar_user is None:
            await ctx.respond("You do not have a role yet.\n"
                              "> Make one by typing `/maaldar create`")
            return

        role = ctx.guild.get_role(int(maaldar_user[1]))

        if not assignee:
            await ctx.author.remove_roles(role)
            await ctx.respond(f"Role unassigned from you")
            return

        await assignee.remove_roles(role)
        await ctx.respond(f"Role unassigned from **{assignee.name}**")


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
        try:
            if self.values[0] == "Yes" and interaction.user == self.assignee:
                await self.assignee.add_roles(self.role)
                await interaction.response.send_message("The role has been assigned to you")

                await self.view.stop()

            if self.values[0] == "No" and interaction.user == self.assignee:
                await self.view.stop()

        except TypeError:
            pass


class DropdownView(discord.ui.View):
    def __init__(self, assignee, role):
        super().__init__()

        self.add_item(Dropdown(assignee, role))


def setup(bot):
    bot.add_cog(Assignation(bot))
