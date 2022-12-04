from discord import Message,Member,Embed
from utils.tyrantlib import split_list
from discord.ext.commands import Cog
from discord.errors import NotFound
from datetime import datetime
from main import client_cls
from re import findall


class logging_listeners(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.recently_deleted = []

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if not message.guild: return
		guild_data = await self.client.db.guilds.read(message.guild.id)
		if not guild_data['config']['logging']['enabled']: return
		if guild_data['config']['logging']['log_all_messages']: await self.log(message)
		regex = guild_data['data']['regex']

		try: regex['channel'][str(message.channel.id)]
		except KeyError: regex['channel'][str(message.channel.id)] = []

		for expression in regex['guild']+regex['channel'][str(message.channel.id)]:
			if findall(expression,message.content):
				self.recently_deleted.append(message.id)
				await message.delete()

				if (
					not guild_data['config']['logging']['channel'] or
					not guild_data['config']['logging']['filtered_messages'] or
					guild_data['config']['logging']['log_bots'] and message.author.bot):
					await self.log(message)
					return
				
				embed = Embed(title=f'message filtered in {message.channel.name}',
				description=f'[jump to channel](<{message.channel.jump_url}>)\n[{str(message.author).lower()}\'s profile](<{message.author.jump_url}>)\n',
				color=0xff6969)
				embed.set_author(name=message.author.display_name,icon_url=message.author.display_avatar.url)
				embed.set_footer(text=f'message id: {message.id}\nuser id:    {message.author.id}')
				embed.add_field(name=f'DELETED  <t:{int(message.created_at.timestamp())}:t>',value=(message.content if len(message.content) <= 1024 else f'{message.content[:1021]}...') or '​',inline=False)
				
				log_msg = await self.client.get_channel(guild_data['config']['logging']['channel']).send(embed=embed)
				await self.log(message,log_message=log_msg)

	@Cog.listener()
	async def on_message_edit(self,before:Message,after:Message) -> None:
		if not before.guild or before.content == after.content: return
		guild_data = await self.client.db.guilds.read(before.guild.id)
		if not guild_data['config']['logging']['enabled']: return
		
		regex = guild_data['data']['regex']

		try: regex['channel'][str(after.channel.id)]
		except KeyError: regex['channel'][str(after.channel.id)] = []

		for expression in regex['guild']+regex['channel'][str(after.channel.id)]:
			if findall(expression,after.content):
				await after.delete()

		if (
			not guild_data['config']['logging']['channel'] or
			not guild_data['config']['logging']['edited_messages'] or
			guild_data['config']['logging']['log_bots'] and before.author.bot):
			await self.log(before,after)
			return
		
		if before.reference:
			try:
				replying_to:Message = self.client.get_message(before.reference.message_id) or await before.channel.fetch_message(before.reference.message_id)
			except NotFound: replying_to = None
		else: replying_to = None
		reply_jmp = None if replying_to is None else f'[replying to {str(replying_to.author).lower()}](<{replying_to.jump_url}>)\n'


		embed = Embed(title=f'edited a message in {before.channel.name}',
		description=f'[jump to channel](<{before.channel.jump_url}>)\n[jump to message](<{before.jump_url}>)\n{reply_jmp or ""}[{str(before.author).lower()}\'s profile](<{before.author.jump_url}>)\n',
		color=0xffff69)
		embed.set_author(name=before.author.display_name,icon_url=before.author.display_avatar.url)
		embed.set_footer(text=f'message id: {before.id}\nuser id:    {before.author.id}')
		if before.edited_at is not None:
			embed.description += '\n\nthis message has been edited before. use /get_log by_id or right click -> Apps -> message data to see full details'
		embed.add_field(name=f'ORIGINAL <t:{int((before.edited_at or before.created_at).timestamp())}:t>',value=(before.content if len(before.content) <= 1024 else f'{before.content[:1021]}...') or '​',inline=False)
		embed.add_field(name=f'EDITED   <t:{int((after.edited_at or after.created_at).timestamp())}:t>',value=(after.content if len(after.content) <= 1024 else f'{after.content[:1021]}...') or '​',inline=False)
		
		log_msg = await self.client.get_channel(guild_data['config']['logging']['channel']).send(embed=embed)
		await self.log(before,after,log_message=log_msg)
	
	@Cog.listener()
	async def on_message_delete(self,message:Message) -> None:
		if message.author == client_cls.user: return
		deleted_at = datetime.now()
		if message.id in self.recently_deleted:
			self.recently_deleted.remove(message.id)
			return
		if not message.guild: return

		guild_data = await self.client.db.guilds.read(message.guild.id)
		if not guild_data['config']['logging']['enabled']: return

		if (
			not guild_data['config']['logging']['channel'] or
			not guild_data['config']['logging']['deleted_messages'] or
			guild_data['config']['logging']['log_bots'] and message.author.bot):
			await self.log(message,deleted_at=deleted_at)
			return

		if message.reference:
			try:
				replying_to:Message = self.client.get_message(message.reference.message_id) or await message.channel.fetch_message(message.reference.message_id)
			except NotFound: replying_to = None
		else: replying_to = None

		reply_jmp = None if replying_to is None else f'[replying to {str(replying_to.author).lower()}](<{replying_to.jump_url}>)\n'

		embed = Embed(title=f'deleted a message in {message.channel.name}',
		description=f'[jump to channel](<{message.channel.jump_url}>)\n{reply_jmp or ""}[{str(message.author).lower()}\'s profile](<{message.author.jump_url}>)\n',
		color=0xff6969)
		embed.set_author(name=message.author.display_name,icon_url=message.author.display_avatar.url)
		embed.set_footer(text=f'message id: {message.id}\nuser id:    {message.author.id}')
		embed.add_field(name=f'DELETED  <t:{int(deleted_at.timestamp())}:t>',value=(message.content if len(message.content) <= 1024 else f'{message.content[:1021]}...') or '​',inline=False)
		if message.attachments:
			
			embed.add_field(name='attachments',value='\n'.join([a.filename for a in message.attachments]),inline=False)

		log_msg = await self.client.get_channel(guild_data['config']['logging']['channel']).send(embed=embed)
		await self.log(message,deleted_at=deleted_at,log_message=log_msg)

	@Cog.listener()
	async def on_bulk_message_delete(self,messages:list[Message]) -> None:
		deleted_at = datetime.now()
		if not messages[0].guild: return
		guild_data = await self.client.db.guilds.read(messages[0].guild.id)
		if not guild_data['config']['logging']['enabled']: return

		if (
			not guild_data['config']['logging']['channel'] or
			not guild_data['config']['logging']['deleted_messages'] or
			guild_data['config']['logging']['log_bots'] and message[0].author.bot):
			for message in messages: await self.log(message)
			return
		
		embed = Embed(title=f'{len(messages)} messages were bulk deleted in {messages[0].channel.name}',
		description=f'[jump to channel](<{messages[0].channel.jump_url}>)\n',
		color=0xff6969)
		for chunk in split_list([str(m.id) for m in messages],48):
			embed.add_field(name=f'DELETED <t:{int(deleted_at.timestamp())}:t>',value='\n'.join(chunk))

		log_msg = await self.client.get_channel(guild_data['config']['logging']['channel']).send(embed=embed)
		for message in messages: await self.log(message,deleted_at=deleted_at,log_message=log_msg)

	@Cog.listener()
	async def on_member_join(self,member:Member) -> None:
		guild_data = await self.client.db.guilds.read(member.guild.id)

		if guild_data['config']['logging']['channel'] and guild_data['config']['logging']['member_join']:
			embed = Embed(
				title=f'{member.name} joined the server',
				description=f"""id: {member.id}
				username: {member.name}
				discriminator: {member.discriminator}""",
				color=0x69ff69)
			embed.set_thumbnail(url=member.display_avatar.with_size(512).with_format('png').url)
			await self.client.get_channel(guild_data['config']['logging']['channel']).send(embed=embed)

	@Cog.listener()
	async def on_member_remove(self,member:Member) -> None:
		guild_data = await self.client.db.guilds.read(member.guild.id)
		
		if guild_data['config']['logging']['channel'] and guild_data['config']['logging']['member_leave']:
			embed = Embed(
				title=f'{member.name} left the server',
				description=f"""id: {member.id}
				username: {member.name}
				discriminator: {member.discriminator}""",
				color=0xff6969)
			embed.set_thumbnail(url=member.display_avatar.with_size(512).with_format('png').url)
			await self.client.get_channel(guild_data['config']['logging']['channel']).send(embed=embed)

	async def log(self,message:Message,after_message:Message=None,deleted_at:datetime=None,log_message:Message=None) -> None:
		if message.author == self.client.user: return
		response = await self.client.db.messages.read(message.id)

		if response is None:
			response = {
				'_id':message.id,
				'author':message.author.id,
				'guild':message.guild.id,
				'channel':message.channel.id,
				'reply_to':0 if message.reference is None else message.reference.message_id,
				'log_message':[] if log_message is None else [log_message.id],
				'logs':[[int(message.created_at.timestamp()),'original',message.content]],
				'attachments':[a.filename for a in message.attachments]}
			if after_message is not None:
				response['logs'].append([int(after_message.edited_at.timestamp()),'edited',after_message.content])
			if deleted_at is not None:
				response['logs'].append([int(deleted_at.timestamp()),'deleted',message.content])
			await self.client.db.messages.new(message.id,response)
		else:
			if after_message is not None:
				await self.client.db.messages.append(message.id,['logs'],[int(after_message.edited_at.timestamp()),'edited',after_message.content])
			if deleted_at is not None:
				await self.client.db.messages.append(message.id,['logs'],[int(deleted_at.timestamp()),'deleted',message.content])
			if log_message is not None:
				await self.client.db.messages.append(message.id,['log_message'],log_message.id)