from discord import Message,Member,Embed,TextChannel,RawMessageUpdateEvent,RawMessageDeleteEvent,RawBulkMessageDeleteEvent,Guild,User,MessageReference
from discord.errors import NotFound,Forbidden
from discord.utils import snowflake_time
from datetime import datetime,timedelta
from asyncio import create_task,sleep
from discord.ext.commands import Cog
from utils.tyrantlib import ArbitraryClass
from client import Client
from time import time
from .embeds import EditLogEmbed,DeleteLogEmbedFromMessage,DeleteLogEmbedFromID
from .config import register_config


class ExtensionLogging(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		register_config(self.client.config)
		self.cached_counts = {}

	async def get_logging_channel(self,guild_id:int) -> TextChannel|None:
		if (guild:=self.client.get_guild(guild_id)) is None: return None
		logging_config = (await self.client.db.guild(guild.id)).config.logging
		if logging_config.enabled is False: return None
		if logging_config.channel is None: return None
		return guild.get_channel(logging_config.channel) or await guild.fetch_channel(logging_config.channel)

	async def from_raw_edit(self,data:dict) -> Message|None:
		_guild = self.client.get_guild(data.get('guild_id')) or await self.client.fetch_guild(data.get('guild_id'))
		_channel = _guild.get_channel(data.get('channel_id')) or await _guild.fetch_channel(data.get('channel_id'))
		message = self.client.get_message(data.get('id')) or await _channel.fetch_message(data.get('id'))
		if message is None: return None
		message.content = data.get('content')
		ts = data.get('edited_timestamp')
		message._edited_timestamp = datetime.fromisoformat(ts) if ts is not None else None
		return message

	async def find_deleter_from_message(self,message:Message) -> Member:
		if message.guild.me.guild_permissions.view_audit_log is False: return None
		async for log in message.guild.audit_logs(after=datetime.now()-timedelta(minutes=5),oldest_first=False):
			if (
				log.action.name == 'message_delete' and
				log.target.id == message.author.id and
				log.extra.channel.id == message.channel.id and
				log.extra.count <= self.cached_counts.get(f'{message.channel.id}{log.target.id}',log.extra.count-1)+1
			):
				self.cached_counts.update({f'{message.channel.id}{log.target.id}':log.extra.count})
				return log.user
		return message.author

	async def find_deleter_from_id(self,message:int,guild:Guild,channel_id:int) -> tuple[Member,Member]|tuple[None,None]:
		if guild.me.guild_permissions.view_audit_log is False: return None
		async for log in guild.audit_logs(after=datetime.now()-timedelta(minutes=5),oldest_first=False):
			if (
				log.action.name == 'message_delete' and
				log.extra.channel.id == channel_id and
				log.extra.count <= self.cached_counts.get(f'{channel_id}{log.target.id}',log.extra.count-1)+1
			):
				self.cached_counts.update({f'{channel_id}{log.target.id}':log.extra.count})
				return log.user,log.target
		return None,None

	@Cog.listener()
	async def on_raw_message_edit(self,payload:RawMessageUpdateEvent) -> None:
		if payload.guild_id is None: return
		log_channel = await self.get_logging_channel(payload.guild_id)
		if log_channel is None: return
		if payload.data.get('author',None) is None: return
		before = payload.cached_message
		after = await self.from_raw_edit(payload.data)
		if after is None: return
		await log_channel.send(embed=EditLogEmbed(after,before))

	@Cog.listener()
	async def on_raw_message_delete(self,payload:RawMessageDeleteEvent) -> None:
		guild = self.client.get_guild(payload.guild_id)
		if guild is None: return
		log_channel = await self.get_logging_channel(payload.guild_id)
		if log_channel is None: return

		if payload.cached_message is not None:
			deleter = await self.find_deleter_from_message(payload.cached_message)
			await log_channel.send(embed=DeleteLogEmbedFromMessage(payload.cached_message,deleter))
			return

		deleter,author = await self.find_deleter_from_id(payload.message_id,guild,payload.channel_id) 
		await log_channel.send(
			embed=DeleteLogEmbedFromID(payload.message_id,payload.channel_id,payload.guild_id,author,deleter))

		return





















def setup(client:Client) -> None:
	client.add_cog(ExtensionLogging(client))
