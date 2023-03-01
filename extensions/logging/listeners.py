from discord import Message,Member,Embed,TextChannel,RawMessageUpdateEvent,RawMessageDeleteEvent,RawBulkMessageDeleteEvent
from utils.db.mongo_object import ReadPathError
from discord.errors import NotFound,Forbidden
from utils.classes import MakeshiftClass
from discord.utils import snowflake_time
from datetime import datetime,timedelta
from discord.ext.commands import Cog
from client import Client
from .utils import utils


class logging_listeners(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.utils = utils(client)
		self.cached_counts = {}

	async def log(
		self,
		_id:int,
		author:int,
		guild:int,
		channel:int,
		reply_to:int=None,
		deleted_by:int=None,
		log:tuple[int,str,str]=None,
		attachments:list[str]=None
	) -> None:
		if self.client.MODE in ['dev','beta']: return
		if await self.client.db.message(_id).read() is not None:
			await self.client.db.message(_id).logs.append(list(log))
			if deleted_by is not None: await self.client.db.message(_id).deleted_by.write(deleted_by)
			return
		await self.client.db.message(0).new(_id,{
			'_id':_id,
			'author':author,
			'guild':guild,
			'channel':channel,
			'reply_to':reply_to,
			'deleted_by':deleted_by,
			'log_messages':[],
			'logs':[log],
			'attachments':attachments})

	async def send_embed(self,message_id:int,channel:TextChannel,limit:int=25) -> None:
		embed = await self.utils.gen_embed(channel.guild,message_id,limit)
		log_message = await channel.send(embed=embed)
		await self.client.db.message(message_id).log_messages.append(log_message.id)

	async def log_check(self,message:Message|Member,mode:str) -> tuple[int,TextChannel|None]:
		if message.guild is None: return (0,None)
		config:dict = await self.client.db.guild(message.guild.id).config.logging.read()
		if not config.get('enabled') or not config.get(mode,False): return (0,None)
		if (config.get('log_bots') and message.author.bot): return (0,None)
		if (channel:=config.get('channel',None)) is not None:
			try: channel = message.guild.get_channel(channel) or await message.guild.fetch_channel(channel)
			except (NotFound,Forbidden): channel = None
		if channel is None: return (1,None)
		if isinstance(message,Message):
			if message.author.id == self.client.user.id and channel.id == message.channel.id: return (1,None)
		return (2,channel)

	async def find_deleter(self,message:Message) -> Member|None:
		if not message.guild.me.guild_permissions.view_audit_log: return None
		async for log in message.guild.audit_logs(after=datetime.now()-timedelta(minutes=6),oldest_first=False):
			if (log.action.name == "message_delete" and
					log.target.id == message.author.id and
					datetime.now().timestamp()-log.created_at.timestamp()<300 and
					log.extra.channel.id == message.channel.id and
					log.extra.count <= self.cached_counts.get(f'{message.channel.id}{log.target.id}',log.extra.count-1)+1
				):
				self.cached_counts.update({f'{message.channel.id}{log.target.id}':log.extra.count})
				return log.user
		return message.author

	async def from_raw(self,data:dict) -> Message:
		_guild = self.client.get_guild(data.get('guild_id')) or await self.client.fetch_guild(data.get('guild_id'))
		message = MakeshiftClass(
			id=int(data.get('id')),
			author=MakeshiftClass(id=int(data.get('author',{}).get('id')),bot=False),
			guild=_guild,
			channel=_guild.get_channel(data.get('channel_id')) or await _guild.fetch_channel(data.get('channel_id')),
			reference=MakeshiftClass(message_id=int(reference.get('message_id'))) if (reference:=data.get('message_reference')) else None,
			created_at=snowflake_time(int(data.get('id'))),
			content=data.get('content'),
			attachments=[MakeshiftClass(filename=a.get('filename')) for a in data.get('attachments',{})])
		return message

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if not (await self.log_check(message,'log_all_messages'))[0]: return
		await self.log(message.id,message.author.id,message.guild.id,message.channel.id,
			message.reference.message_id if message.reference else None,None,
			[int(message.created_at.timestamp()),'original',message.content],
			[att.filename for att in message.attachments])

	@Cog.listener()
	async def on_raw_message_edit(self,payload:RawMessageUpdateEvent) -> None:
		if payload.guild_id is None: return
		if payload.data.get('author',None) is None: return
		before = payload.cached_message
		after  = await self.from_raw(payload.data)
		if before is None or after is None:
			await self.client.log.debug('raw message edit error',payload=dict(payload.data))
			return
		check,channel = await self.log_check(before or after,'edited_messages')
		if not check: return
		if before is not None:
			if before.content == after.content: return
			if await self.client.db.message(before.id).read() is None:
				await self.log(before.id,before.author.id,before.guild.id,before.channel.id,
					before.reference.message_id if before.reference else None,None,
					[int(before.created_at.timestamp()),'original',before.content],
					[att.filename for att in before.attachments])
		await self.log(after.id,after.author.id,after.guild.id,after.channel.id,
			after.reference.message_id if after.reference else None,None,
			[int(datetime.now().timestamp()),'edited',after.content],
			[att.filename for att in after.attachments])
		if check <= 1: return
		try: await self.send_embed(after.id,channel,2)
		except ValueError: return

	@Cog.listener()
	async def on_raw_message_delete(self,payload:RawMessageDeleteEvent) -> None:
		if payload.guild_id is None: return
		message = payload.cached_message or MakeshiftClass(
			guild=self.client.get_guild(int(payload.guild_id)) or await self.client.fetch_guild(int(payload.guild_id)),
			channel=MakeshiftClass(id=int(payload.channel_id)),
			author=MakeshiftClass(id=None,bot=False))
		check,channel = await self.log_check(message,'deleted_messages')
		if not check: return
		if await self.client.db.guild(int(payload.guild_id)).config.general.pluralkit.read():
			if await self.client.pk.get_message(int(payload.message_id),5,False) is not None: check = 1
		if payload.cached_message is None:
			try: log = await self.client.db.message(int(payload.message_id)).read()
			except ReadPathError: return
			if log is None: return
			await self.client.db.message(int(payload.message_id)).logs.append([int(datetime.now().timestamp()),'deleted',log.get('logs',[[None]])[-1][-1]])
		else:
			await self.log(message.id,message.author.id,message.guild.id,message.channel.id,
			message.reference.message_id if message.reference else None,(await self.find_deleter(message)).id,
			[int(datetime.now().timestamp()),'deleted',message.content],
			[att.filename for att in message.attachments])
		if check <= 1: return
		try: await self.send_embed(int(payload.message_id),channel,1)
		except ValueError: return

	@Cog.listener()
	async def on_raw_bulk_message_delete(self,payload:RawBulkMessageDeleteEvent) -> None:
		check,channel = await self.log_check(MakeshiftClass(
			guild=self.client.get_guild(int(payload.guild_id)) or await self.client.fetch_guild(int(payload.guild_id)),
			channel=MakeshiftClass(id=int(payload.channel_id)),
			author=MakeshiftClass(id=None,bot=False)),'deleted_messages')
		if not check: return
		deleted_at = int(datetime.now().timestamp())
		m_ids = list(payload.message_ids)
		for message_id in m_ids:
			try: log = await self.client.db.message(message_id).read()
			except ReadPathError: continue
			if log is None: continue
			await self.client.db.message(message_id).logs.append([deleted_at,'deleted',log.get('logs',[[None]])[-1][-1]])
		if check <= 1: return
		embed = Embed(title=f'{len(m_ids)} messages bulk deleted in <#{payload.channel_id}>',description=','.join([str(i) for i in m_ids]),color=0xff6969)
		await channel.send(embed=embed)

	@Cog.listener()
	async def on_member_join(self,member:Member) -> None:
		check,channel = await self.log_check(member,'member_join')
		if check <= 1: return
		embed = Embed(title=f'{member.name} joined the server',color=0x69ff69)
		embed.add_field(name='id',value=member.id,inline=False)
		embed.add_field(name='username',value=member.name,inline=False)
		embed.add_field(name='discriminator',value=member.discriminator,inline=False)
		embed.set_thumbnail(url=member.display_avatar.with_size(512).with_format('png').url)
		await channel.send(embed=embed)

	@Cog.listener()
	async def on_member_remove(self,member:Member) -> None:
		check,channel = await self.log_check(member,'member_leave')
		if check <= 1: return
		embed = Embed(title=f'{member.name} left the server',color=0xff6969)
		embed.add_field(name='id',value=member.id,inline=False)
		embed.add_field(name='username',value=member.name,inline=False)
		embed.add_field(name='discriminator',value=member.discriminator,inline=False)
		embed.set_thumbnail(url=member.display_avatar.with_size(512).with_format('png').url)
		await channel.send(embed=embed)