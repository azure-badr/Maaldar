import discord
from discord.ext import commands

from util import configuration, select_one, insert_query, delete_query

from datetime import datetime, timedelta

class BoostEvent(commands.Cog):
  DAYS_REQUIRED_FOR_ROLE = 180

  def __init__(self, bot):
    self.bot = bot
  
  def _check_and_update_duration(self, member_id: str, boosting_since: timedelta) -> None:
    data = select_one(f"SELECT * FROM MaaldarDuration WHERE user_id = '{member_id}'")
    if data is None:
      insert_query(f"INSERT INTO MaaldarDuration VALUES ('{member_id}', '{boosting_since}')")
      return
    
    insert_query(
      f"UPDATE MaaldarDuration SET boosting_since = boosting_since + '{boosting_since}' "
      f"WHERE user_id = '{member_id}'"
    )
  
  @commands.Cog.listener()
  async def on_member_update(self, before: discord.Member, after: discord.Member):
    member = before

    # @DEVELOPMENT - This is for testing purposes only
    # guild = before.guild
    # maaldar_role = guild.get_role(configuration["custom_role_id"])
    # if maaldar_role not in after.roles and maaldar_role in before.roles:
    #   self.cursor.execute(
    #     f"UPDATE MaaldarDuration SET boosting_since = boosting_since + '115 days, 7:07:47.776831' "
    #     f"WHERE user_id = '{member.id}'"
    #   )
    #   self.connection.commit()
    
    # If member was not boosting before, return
    if before.premium_since is None:
      return
    
    # If member has started boosting
    if after.premium_since is not None:
      maaldar_role = select_one(f"SELECT * FROM MaaldarRoles WHERE user_id = '{member.id}'")
      if maaldar_role is None:
        return
      
      if len(after.guild.roles) == 250:
        return

      guild = after.guild
      # Create the role according to user data and position it
      role = await guild.create_role(
        name=maaldar_role[1], 
        color=discord.Color(int(maaldar_role[2]))
      )

      await role.edit(
        position=(guild.get_role(configuration["custom_role_id"]).position - 1)
      )
      await member.add_roles(role)

      insert_query(
        f"INSERT INTO Maaldar VALUES ('{member.id}', '{role.id}')"
      )
      
      return
    
    """
    If member has stopped boosting
    This part handles the case when member has stopped boosting and
    if the member has not boosted for 180 days total, the role is removed
    """

    # Setting member.premium_since.tzinfo to None to avoid naive and aware datetime comparison
    boosting_since = datetime.now() - before.premium_since.replace(tzinfo=None)
    self._check_and_update_duration(member.id, boosting_since)
    
    boosting_since = select_one(
      f"SELECT boosting_since FROM MaaldarDuration WHERE user_id = '{member.id}'"
    ) # timedelta object
    
    if boosting_since[0] >= timedelta(days=self.DAYS_REQUIRED_FOR_ROLE):
      return
    
    data = select_one(f"SELECT role_id FROM Maaldar WHERE user_id = '{member.id}'")
    if data is None:
      return
    
    role_id = data[0]
    role = member.guild.get_role(int(role_id))

    await member.remove_roles(role)

    delete_query(
      f"DELETE FROM Maaldar WHERE user_id = '{member.id}';"
    )

async def setup(bot: commands.Bot):
  await bot.add_cog(BoostEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
