from discord.ext import commands

from util import update_role_position


class GuildRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_create(self, _):
        update_role_position("increment")

    @commands.Cog.listener()
    async def on_guild_role_remove(self, _):
        update_role_position("decrement")


def setup(bot):
    bot.add_cog(GuildRole(bot))
