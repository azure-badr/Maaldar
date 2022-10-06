import asyncio
import sqlite3
import uuid

import discord
from discord.ext import commands


class Color(commands.Cog):
    connection = sqlite3.connect("maaldar.db")
    cursor = connection.cursor()

    @staticmethod
    async def create_session(interaction):
        session = uuid.uuid4().hex
        Color.cursor.execute(
            "INSERT INTO MaaldarSession VALUES (?, ?)", (interaction.user.id, session)
        )
        Color.connection.commit()
        await interaction.followup.send("Created session, please check your DM")

        try:
            await interaction.user.send(
                "Session created ✨\n" f"> http://pakcord.mooo.com/{session}"
            )
            """Wait for 1 hour and delete session"""
            await asyncio.sleep(3600)
            Color.cursor.execute(
                "DELETE FROM MaaldarSession WHERE user_id = ?", (interaction.user.id,)
            )
            Color.connection.commit()

        except discord.Forbidden:
            await interaction.followup.send("Please enable your DMs")
            Color.cursor.execute(
                "DELETE FROM MaaldarSession WHERE user_id = ?", (interaction.user.id,)
            )
            Color.connection.commit()
