from discord.commands import Permission
import os

from util import configuration

import discord

intents = discord.Intents(members=True, guilds=True)
bot = discord.Bot(intents=intents)

maaldar = bot.create_group(
    "maaldar",
    "Commands for the Maaldar booster role",
    configuration["guild_ids"]
)
maaldar.permissions = [Permission(role_id, 1, True)
                       for role_id in configuration["role_ids"]]
maaldar.default_permission = False

for module in os.listdir("./modules"):
    if module.endswith(".py"):
        bot.load_extension(f"modules.{module[:-3]}")
        print(f"{module} loaded")

for event in os.listdir("./events"):
    if event.endswith(".py"):
        bot.load_extension(f"events.{event[:-3]}")
        print(f"{event} loaded")

bot.run(configuration["token"])
