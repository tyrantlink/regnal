from .subcog import ExtensionActivityRolesSubCog
from .models import ActivityRoleChanges
from discord import Guild,Embed


class ExtensionActivityRolesLogic(ExtensionActivityRolesSubCog):
	async def new_day(self,guild:Guild) -> ActivityRoleChanges:
		guild_doc = await self.client.db.guild(guild.id)
		if guild_doc is None:
			return
		if not len(guild_doc.data.activity) > 0:
			return
		if not guild_doc.config.activity_roles.enabled:
			return
		if guild_doc.config.activity_roles.role is None:
			return
		next_day = guild_doc.get_day_in(minutes=20)
		if not (next_day > guild_doc.data.activity_roles.last_day):
			return

		role = guild.get_role(guild_doc.config.activity_roles.role)
		if role is None:
			return

		ignored_roles = set(guild_doc.config.activity_roles.ignored_roles)

		lookback_list = list(
			dict(
				sorted(
					{
						int(day):value
						for day,value in
						guild_doc.data.activity.items()
					}.items(),
				reverse=True
				)
			).values()
		)[:guild_doc.config.activity_roles.timeframe]

		totals = {}
		for day in lookback_list:
			for user_id, message_count in day.items():
				if user_id not in totals:
					totals[user_id] = 0
				totals[user_id] += message_count

		users = set()
		for member_id in sorted(totals.keys(),key=lambda x: totals[x],reverse=True):
			member = guild.get_member(int(member_id))
			if member is None or {r.id for r in member.roles} & ignored_roles:
				continue
			users.add(member)
			if len(users) >= guild_doc.config.activity_roles.max_roles:
				break

		changes = ActivityRoleChanges()

		for user in role.members:
			if user not in users:
				changes.removed.add(user)
				await user.remove_roles(role)

		for user in users:
			if role not in user.roles:
				changes.added.add(user)
				await user.add_roles(role)
		
		changes.unchanged = (users - changes.added) - changes.removed

		guild_doc.data.activity_roles.last_day = next_day
		await guild_doc.save_changes()

		return changes

	async def log_changes(self,guild:Guild,changes:ActivityRoleChanges) -> None:
		if not changes.added and not changes.removed:
			return

		guild_doc = await self.client.db.guild(guild.id)
		if not guild_doc.config.logging.activity_roles:
			return
		if not guild_doc.config.logging.enabled:
			return
		if guild_doc.config.logging.channel is None:
			return

		logging_channel =	guild.get_channel(guild_doc.config.logging.channel)

		embed = Embed(title='activity role changes',color=await self.client.helpers.embed_color(guild.id))
		if changes.unchanged:
			embed.add_field(
				name='unchanged',
				value='\n'.join(
					[f'{user.mention}' for user in changes.unchanged]
				),
				inline=False)
		if changes.added:
			embed.add_field(
				name='added',
				value='\n'.join(
					[f'{user.mention}' for user in changes.added]
				),
				inline=False)
		if changes.removed:
			embed.add_field(
				name='removed',
				value='\n'.join(
					[f'{user.mention}' for user in changes.removed]
				),
				inline=False)
		embed.set_footer(
			text=f'day {guild_doc.get_current_day()} users: {changes.total_users}/{guild_doc.config.activity_roles.max_roles}')

		await logging_channel.send(embed=embed)