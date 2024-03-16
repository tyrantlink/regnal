from utils.db.documents import Guild as GuildDocument
from .subcog import ExtensionTalkingStickSubCog
from asyncio import sleep,create_task
from time import perf_counter,time
from typing import AsyncIterator
from discord import Embed,Guild
from random import choice

class ExtensionTalkingStickLogic(ExtensionTalkingStickSubCog):
	async def find_guilds(self) -> AsyncIterator[tuple[Guild,GuildDocument]]:
		if not self._rescan and time()-self._guilds[0] < 60:
			for guild in self._guilds[1]:
				if guild[1].id in self.recently_rolled: continue
				yield guild
			return
		_client_guilds = {guild.id for guild in self.client.guilds}

		guilds = list()
		async for guild in self.client.db._client.guilds.find(
			# ensure talking stick is enabled
			{'config.talking_stick.enabled':True,
			'config.talking_stick.channel':{'$ne':None},
			'config.talking_stick.role':{'$ne':None}}
			# ensure guild is attached to current shard and not in recently rolled
		):
			if guild['_id'] not in _client_guilds or guild['_id'] in self.recently_rolled: continue
			guild = self.client.get_guild(guild['_id']) or await self.client.fetch_guild(guild['_id'])
			if guild is None: continue
			guild_doc = await self.client.db.guild(guild.id)
			# ensure guild data exists and stick is only rolled once per day
			if guild_doc is None or guild_doc.data.talking_stick.last == guild_doc.get_current_day()-1: continue
			guilds.append((guild,guild_doc))
			yield guild,guild_doc
		self._guilds = (time(),guilds)
		self._rescan = False

	async def roll_complete(self,guild_id:int) -> None:
		await sleep(300)
		self.recently_rolled.remove(guild_id)

	async def roll_talking_stick(self,guild:Guild,guild_doc:GuildDocument) -> bool:
		current_day = guild_doc.get_current_day()-1
		# get stick role
		role = guild.get_role(guild_doc.config.talking_stick.role) if guild_doc.config.talking_stick.role else None
		if role is None: return False
		# get stick channel
		channel = guild.get_channel(guild_doc.config.talking_stick.channel) if guild_doc.config.talking_stick.channel else None
		# get current stick
		current_stick = guild.get_member(guild_doc.data.talking_stick.current) if guild_doc.data.talking_stick.current else None
		# get active members
		active = {int(user_id) for user_id in guild_doc.data.activity.get(str(current_day),{}).keys()}
		if not active: return False
		# remove current stick from options

		if current_stick is not None and current_stick.id in active: active.remove(current_stick.id)
		# remove users without limit role
		if guild_doc.config.talking_stick.limit is not None:
			limit_role = guild.get_role(guild_doc.config.talking_stick.limit)
			if limit_role is not None:
				members = {member.id for member in limit_role.members}
				options = {user_id for user_id in active if user_id in members}
		else: options = active.copy()
		# remove users with talking stick disabled
		for user_id in active:
			user_data = await self.client.db.user(int(user_id))
			if user_data is None or not user_data.config.general.talking_stick:
				options.remove(user_id)
		# ensure there are options
		if not options: return False
		self.client.log.debug(f'ts options: {options}')

		member_list = dict(
			sorted({k:v for k,v in {
				member_id:guild.get_member(member_id) or
				await guild.fetch_member(member_id)
				for member_id in active
			}.items() if v is not None}.items(),
			key=lambda m: len(m[1].display_name),
			reverse=True))
		# roll new stick
		for _ in range(10): # looping shouldn't be necessary with the number of checks above, but i'm paranoid
			rand = choice(list(options))
			new_stick = member_list.get(rand,None)
			if new_stick is None: continue
			break
		else: return False
		# remove existing sticks
		for member in role.members:
			await member.remove_roles(role,reason='no longer has talking stick')
		# give new stick
		await new_stick.add_roles(role,reason='has talking stick')
		self.client.log.info(f'{new_stick.name} received talking stick in {guild.name}',guild.id)
		# send message
		await channel.send(
			guild_doc.config.talking_stick.announcement_message.replace('{user}',new_stick.mention),
			embed=Embed(
				title=f'{1/len(member_list):.2%} chance (1/{len(member_list)})',
				description='\n'.join(
					[new_stick.mention,'']+
					[f'{member.mention}'
					for member in member_list.values()
					if member.id != new_stick.id]),
				color=await self.client.helpers.embed_color(guild.id)))
		# update guild data
		guild_doc.data.talking_stick.current = new_stick.id
		guild_doc.data.talking_stick.last = current_day

		self.recently_rolled.add(guild.id)
		create_task(self.roll_complete(guild.id))
		self._rescan = True
		await guild_doc.save_changes()
		return True