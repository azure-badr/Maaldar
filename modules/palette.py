import discord
from discord.ext import commands, tasks
from discord.commands import permissions

from util import configuration, check_if_user_exists, rgb_to_hex, make_image, concatenate_images, clean_up
from main import maaldar

import io
import asyncio
import sqlite3
import aiohttp

from colorthief import ColorThief


class Palette(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    usage = 0
    cooldowns = []

    async def cooldown(author_id):
        Palette.usage += 1
        Palette.cooldowns.append(author_id)
        await asyncio.sleep(3600)
        Palette.cooldowns.remove(author_id)

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.reset_usage.start()

    @maaldar.command()
    @permissions.has_any_role(*configuration["role_ids"])
    async def palette(ctx: discord.ApplicationContext):
        """Gets a color palette for your profile picture"""

        maaldar_user = check_if_user_exists(Palette.cursor, ctx.author.id)
        if maaldar_user is None:
            await ctx.respond("You do not have a role yet.\n"
                              "> Make one by typing `/maaldar create`")
            return

        """Cooldown check"""
        user_reattempt = ctx.author.id in Palette.cooldowns

        """Launch a cooldown on the command executing author"""
        asyncio.ensure_future(Palette.cooldown(ctx.author.id))

        role = ctx.guild.get_role(int(maaldar_user[1]))

        await ctx.defer()
        """Read profile picture from avatar.url"""
        buffer: io.BytesIO
        async with aiohttp.ClientSession() as session:
            async with session.get(ctx.author.avatar.url) as response:
                if response.status == 200:
                    buffer = io.BytesIO(await response.read())

        """Get color palette and make new images with them"""
        color_palette = ColorThief(
            buffer
        ).get_palette(color_count=11)

        hex_values = []
        images = []
        for dominant_color in color_palette:
            hex_values.append(rgb_to_hex(dominant_color))

            image = make_image(dominant_color)
            images.append(image)

        """
        If usage is greater than 5 then use traditional method instead
        of role uploading
        """
        if Palette.usage > 5 or user_reattempt:
            concatenate_images(images)
            await ctx.respond(file=discord.File("./palette.png"))
            clean_up()

            view = DropdownView(hex_values, role, ctx.author)
            await ctx.respond("Choose the color you want", view=view)

            return

        """Convert the images to file-like objects"""
        emojis = []
        for image in images:
            image_byte_array = io.BytesIO()
            image.save(image_byte_array, "PNG")
            emojis.append(
                image_byte_array.getvalue())

        """Add the emojis to the guild"""
        emojis_guild: discord.Guild = ctx.bot.get_guild(
            configuration["emoji_server_id"])
        added_emojis = []

        for index, emoji in enumerate(emojis, start=0):
            added_emojis.append(
                await emojis_guild.create_custom_emoji(
                    name=hex_values[index], image=emoji
                )
            )

        view = DropdownView(hex_values, added_emojis, role, ctx.author)

        await ctx.respond("Choose the color you want", view=view)
        for emoji in added_emojis:
            await emojis_guild.delete_emoji(emoji)

    @tasks.loop(seconds=3500)
    async def reset_usage(self):
        Palette.usage = 0

    @reset_usage.before_loop
    async def before_reset_usage(self):
        await self.bot.wait_until_ready()


class Dropdown(discord.ui.Select):
    def __init__(self, *args):
        if len(args) == 4:
            self.role = args[2]
            self.user = args[3]
            options = [
                discord.SelectOption(
                    label=f"{args[0][index]}", description=f"Color #{index + 1}", emoji=emoji
                ) for index, emoji in enumerate(args[1])
            ]
        else:
            self.role = args[1]
            self.user = args[2]
            options = [
                discord.SelectOption(
                    label=f"#{args[0][index]}", description=f"Color #{index + 1}"
                ) for index in range(10)
            ]

        super().__init__(
            placeholder="Colors",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user == self.user:
                await self.role.edit(
                    color=discord.Color(
                        int(self.values[0][1:], 16)
                    )
                )
                await interaction.response.send_message(
                    f"Set your role color to `{self.values[0].upper()}` ✨"
                )

                await self.view.stop()
        except TypeError:
            pass


class DropdownView(discord.ui.View):
    def __init__(self, *args):
        super().__init__()

        if len(args) == 4:
            self.add_item(Dropdown(args[0], args[1], args[2], args[3]))
            return

        self.add_item(Dropdown(args[0], args[1], args[2]))


def setup(bot):
    bot.add_cog(Palette(bot))
