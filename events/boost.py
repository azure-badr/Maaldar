import discord
from discord.ext import commands

from util import configuration, select_one, insert_query, delete_query, parse_role_colors

from datetime import datetime, timezone

class BoostEvent(commands.Cog):
  # Seconds in 180 days
  DAYS_IN_SECONDS_REQUIRED_FOR_ROLE = 15_552_000

  def __init__(self, bot):
    self.bot = bot
  
  def _credit_duration(self, member_id: str, premium_since: datetime) -> None:
    now = int(datetime.now(timezone.utc).timestamp())
    started = int(premium_since.timestamp())

    data = select_one(f"SELECT last_credited_at FROM MaaldarDuration WHERE user_id = '{member_id}'")
    credited_until = max(data[0] or started, started) if data else started
    earned = max(now - credited_until, 0)

    if data is None:
      insert_query(f"INSERT INTO MaaldarDuration VALUES ('{member_id}', '{earned}', '{now}')")
      return

    if earned <= 0:
      return

    insert_query(
      f"UPDATE MaaldarDuration SET boosting_since = boosting_since + '{earned}', "
      f"last_credited_at = '{now}' WHERE user_id = '{member_id}'"
    )

  @commands.Cog.listener()
  async def on_ready(self) -> None:
    guild = self.bot.get_guild(configuration["guild_id"])
    if guild is None:
      return

    for member in guild.premium_subscribers:
      if member.premium_since is not None:
        self._credit_duration(member.id, member.premium_since)
  
  @commands.Cog.listener()
  async def on_member_update(self, before: discord.Member, after: discord.Member):
    member = before

    nitro_role = member.guild.premium_subscriber_role

    # @DEVELOPMENT - This is for testing purposes only
    # guild = before.guild
    # maaldar_role = guild.get_role(configuration["custom_role_id"])
    # if maaldar_role not in after.roles and maaldar_role in before.roles:
    #   self.cursor.execute(
    #     f"UPDATE MaaldarDuration SET boosting_since = boosting_since + '115 days, 7:07:47.776831' "
    #     f"WHERE user_id = '{member.id}'"
    #   )
    #   self.connection.commit()
    
    # If member has started boosting
    if nitro_role in after.roles and nitro_role not in before.roles:
      print(f"[!] {member} has started boosting")

      if after.premium_since is not None:
        self._credit_duration(member.id, after.premium_since)

      maaldar_role = select_one(f"SELECT * FROM MaaldarRoles WHERE user_id = '{member.id}'")
      if maaldar_role is None:
        return
      
      # Check if user already has a Maaldar role in the server
      data = select_one(f"SELECT * FROM Maaldar WHERE user_id = '{member.id}'")
      if data is not None:
        print("[!] Maaldar role already exists. Skipping...")
        return
      
      if len(after.guild.roles) >= 250:
        print("[!] Role limit reached. Cannot create role.")
        return

      print(f"[!] MaaldarRoles found for {member.name}. Creating role...")
      guild = after.guild
      # Create the role according to user data and position it
      role = await guild.create_role(
        name=maaldar_role[1],
        **parse_role_colors(maaldar_role[2])
      )

      # INVERTED: above=anchor places the role visually BELOW the anchor.
      # See appeal/verify/18_move_semantics.py.
      anchor = guild.get_role(configuration["custom_role_id"])
      try:
        await role.move(above=anchor, reason="maaldar boost")
      except Exception as error:
        # Positioning failed but the role exists and is about to be assigned.
        # Discord creates roles at position 1, so it is now stranded near the
        # bottom of the guild. Tell the owner — the booster cannot self-recover
        # (/maaldar position requires them to already hold another Maaldar role).
        print(f"[!] Failed to position boost role {role.id}: {error}")
        try:
          owner = after.guild.get_member(configuration["owner_id"])
          if owner is not None:
            await owner.send(
              f"[!] Created Maaldar role `{role.name}` ({role.id}) for "
              f"{member.name} but could not position it: {error}\n"
              "It is stranded at the bottom of the role list and needs a manual move."
            )
        except Exception as notify_error:
          print(f"[!] Could not notify owner: {notify_error}")
      await member.add_roles(role)
      print(f"[+] {role.name} created and given to {member.name}")

      insert_query(
        f"INSERT INTO Maaldar VALUES ('{member.id}', '{role.id}')"
      )
      
      return
    
    elif nitro_role not in after.roles and nitro_role in before.roles:
      """
      If member has stopped boosting
      This part handles the case when member has stopped boosting and
      if the member has not boosted for 180 days total, the role is removed
      """
      print(f"[!] {member} has stopped boosting")

      self._credit_duration(member.id, before.premium_since)
      
      boosting_since = select_one(
        f"SELECT boosting_since FROM MaaldarDuration WHERE user_id = '{member.id}'"
      )
      
      if boosting_since[0] >= self.DAYS_IN_SECONDS_REQUIRED_FOR_ROLE:
        print(f"[!] {member} has boosted for {self.DAYS_IN_SECONDS_REQUIRED_FOR_ROLE} days. Keeping role...")
        return
      
      data = select_one(f"SELECT role_id FROM Maaldar WHERE user_id = '{member.id}'")
      if data is None:
        return
      
      print(f"[!] {member} has not boosted for {self.DAYS_IN_SECONDS_REQUIRED_FOR_ROLE} days. Removing role...")
      role_id = data[0]
      role = member.guild.get_role(int(role_id))

      await member.remove_roles(role)
      await role.delete()
      delete_query(
        f"DELETE FROM Maaldar WHERE user_id = '{member.id}'"
      )
      print(f"[-] {role.name} deleted and removed from {member.name}")

async def setup(bot: commands.Bot):
  await bot.add_cog(BoostEvent(bot), guilds=[discord.Object(id=configuration["guild_id"])])
