import discord
from discord.ext import commands

from util import configuration, get_maaldar_user, insert_with_params, is_old_maaldar, select_one, delete_query

class UserLeaveEvent(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  @commands.Cog.listener()
  async def on_member_remove(self, member):
    guild: discord.Guild = member.guild
    
    maaldar_user = get_maaldar_user(member.id)
    if maaldar_user is None:
      return
    
    delete_query(f"DELETE FROM Maaldar WHERE user_id = '{member.id}'")

    role = guild.get_role(int(maaldar_user[1]))

    if is_old_maaldar(member.id):
      maaldar_role = select_one(f"SELECT * FROM MaaldarRoles WHERE user_id = '{member.id}'")
      # If the Maaldar role already exists in the database, update role name and color
      if maaldar_role is None:
        insert_with_params(
          f"INSERT INTO MaaldarRoles VALUES ('{member.id}', %s, %s)",
          (role.name, role.color.value)
        )
      else:
        insert_with_params(
          f"UPDATE MaaldarRoles SET role_name = %s, role_color = %s WHERE user_id = '{member.id}'",
          (role.name, role.color.value)
        )
    
    await role.delete()

async def setup(bot: commands.Bot):
  await bot.add_cog(UserLeaveEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
