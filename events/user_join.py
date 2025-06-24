import discord
import discord.http
from discord.ext import commands

from util import configuration, insert_query, select_one
class UserJoinEvent(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
  
  def _get_payload_from_maaldar_role_color(self, role_color_str: str):
    colors = str(role_color_str).split(',')
    role_color_payload = {}

    if len(colors) == 3:
      primary, secondary, tertiary = colors
      role_color_payload["colors"] = {
        "primary_color": primary,
        "secondary_color": secondary,
        "tertiary_color": tertiary
      }
    elif len(colors) == 2:
      primary, secondary = colors
      role_color_payload["colors"] = {
        "primary_color": primary,
        "secondary_color": secondary
      }
    else:
      role_color_payload["color"] = role_color_str
    
    return role_color_payload
  
  
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

    role = await role.edit(
      position=(guild.get_role(configuration["custom_role_id"]).position - 1)
    )
    
    role_color: str = maaldar_role[2]
    payload = self._get_payload_from_maaldar_role_color(role_color)
    await self.bot.http.request(
      discord.http.Route(
        "PATCH",
        "/guilds/{guild_id}/roles/{role_id}",
        guild_id=member.guild.id,
        role_id=role.id
      ),
      json=payload
    )

    await member.add_roles(role)
    insert_query(
      f"INSERT INTO Maaldar VALUES ('{member.id}', '{role.id}')"
    )
    print(f"[!] Created role {role.id} at position {role.position} and assigned to {member.id}")
  

async def setup(bot: commands.Bot):
  await bot.add_cog(UserJoinEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
