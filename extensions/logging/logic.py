from discord import Message,Member,TextChannel,Guild
from datetime import datetime,timedelta
from utils.pycord_classes import SubCog

class ExtensionLoggingLogic(SubCog):
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

class GuildLogger: ...