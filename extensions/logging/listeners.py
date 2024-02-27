from discord import RawMessageUpdateEvent,RawMessageDeleteEvent,RawBulkMessageDeleteEvent,Embed
from .embeds import EditLogEmbed,DeleteLogEmbedFromMessage,DeleteLogEmbedFromID
from .views import EditedLogView,DeletedLogView,BulkDeletedLogView
from utils.pycord_classes import SubCog
from discord.ext.commands import Cog

class ExtensionLoggingListeners(SubCog):
	@Cog.listener()
	async def on_raw_message_edit(self,payload:RawMessageUpdateEvent) -> None:
		if payload.guild_id is None: return
		log_channel = await self.get_logging_channel(payload.guild_id)
		if log_channel is None: return
		guild_doc = await self.client.db.guild(payload.guild_id)
		if not guild_doc.config.logging.edited_messages: return
		if payload.data.get('author',None) is None: return
		if int(payload.data['author']['id']) == self.client.user.id: return
		before = payload.cached_message or await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
		after = await self.from_raw_edit(payload.data)
		if after is None: return
		if after.author.bot and not guild_doc.config.logging.log_bots: return
		if before is not None and before.content == after.content: return
		await log_channel.send(
			embed=EditLogEmbed(after,before),
			view=EditedLogView(self.client))

	@Cog.listener()
	async def on_raw_message_delete(self,payload:RawMessageDeleteEvent) -> None:
		guild = self.client.get_guild(payload.guild_id)
		if guild is None: return
		if payload.message_id in self.client.logging_ignore:
			self.client.logging_ignore.discard(payload.message_id)
			return
		log_channel = await self.get_logging_channel(payload.guild_id)
		if log_channel is None: return
		guild_doc = await self.client.db.guild(payload.guild_id)
		if not guild_doc.config.logging.deleted_messages: return
		if guild_doc.config.logging.pluralkit_support and await self.deleted_by_pk(payload.message_id): return
		if payload.cached_message is not None:
			if payload.cached_message.author.id == self.client.user.id: return
			if payload.cached_message.author.bot and not guild_doc.config.logging.log_bots: return
			deleter = await self.find_deleter_from_message(payload.cached_message)
			await log_channel.send(
				embed=DeleteLogEmbedFromMessage(payload.cached_message,deleter),
				view=DeletedLogView(self.client,bool(payload.cached_message.attachments)))
			return

		deleter,author = await self.find_deleter_from_id(payload.message_id,guild,payload.channel_id)
		if author is not None and author.id == self.client.user.id: return
		if author is not None and author.bot and not guild_doc.config.logging.log_bots: return
		await log_channel.send(
			embed=DeleteLogEmbedFromID(payload.message_id,payload.channel_id,author,deleter),
			view=DeletedLogView(self.client,False))

	@Cog.listener()
	async def on_raw_bulk_message_delete(self,payload:RawBulkMessageDeleteEvent) -> None:
		if payload.guild_id is None: return
		log_channel = await self.get_logging_channel(payload.guild_id)
		if log_channel is None: return
		if not (await self.client.db.guild(payload.guild_id)).config.logging.deleted_messages: return

		embed = Embed(
			title=f'{len(payload.message_ids)} messages bulk deleted in <#{payload.channel_id}>',
			color=0x69ff69)
		message_ids = ','.join([str(i) for i in payload.message_ids])
		if not len(message_ids) > 4096:
			embed.description = message_ids
			await log_channel.send(embed=embed,view=BulkDeletedLogView(self.client))
			return
		if len(message_ids) > 256000:
			embed.description = 'there\'s actually just too many i can\'t >.<'
			await log_channel.send(embed=embed,view=BulkDeletedLogView(self.client))
			return
		tmp_value = str(payload.message_ids[0])
		index = 1
		for msg_id in payload.message_ids:
			if len(tmp_value)+len(str(msg_id)) > 1023:
				embed.add_field(name=f'message IDs - part {index}',value=tmp_value,inline=False)
				tmp_value = str(msg_id)
				continue
			tmp_value += f',{msg_id}'
		for field in embed.fields:
			field.name += f'/{index}'
		
		await log_channel.send(embed=embed,view=BulkDeletedLogView(self.client))