import discord
import discord.http
from discord.ext import commands

from util import configuration, insert_query, select_one
class UserJoinEvent(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
  
  def _get_colors(self, role_color_str: str):
    color_keys = ["color", "secondary_color", "tertiary_color"]
    colors = role_color_str.split(',')

    return {
        key: int(value)
        for key, value in zip(color_keys, colors)
        if value
    }
  
  
  """
  This event is triggered when a user joins the server,
  and will assign the user their Maaldar role if they are
  an old Maaldar
  """  
  @commands.Cog.listener()
  async def on_member_join(self, member: discord.Member):
    guild: discord.Guild = member.guild

    maaldar_role = select_one(f"SELECT * From MaaldarRoles WHERE user_id = '{member.id}'")
    if maaldar_role is None:
      return
    
    if len(guild.roles) == 250:
      return
    
    print(f"[!] An old Maaldar user {member.id} has joined the server. Recreating their role...")
    role = await guild.create_role(
      name=maaldar_role[1]
    )

    role_color_str: str = maaldar_role[2]
    role_colors = self._get_colors(role_color_str)
    role = await role.edit(
      **role_colors,
      position=(guild.get_role(configuration["custom_role_id"]).position - 1)
    )

    await member.add_roles(role)
    insert_query(
      f"INSERT INTO Maaldar VALUES ('{member.id}', '{role.id}')"
    )
    print(f"[!] Created role {role.id} at position {role.position} and assigned to {member.id}")
  

async def setup(bot: commands.Bot):
  await bot.add_cog(UserJoinEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
