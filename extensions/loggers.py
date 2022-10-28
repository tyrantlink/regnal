from discord import User,TextChannel,File,Message,ApplicationContext,Member,Permissions,Embed,Guild
from discord.commands import SlashCommandGroup,Option as option
from discord.ext.commands import Cog,message_command
from utils.tyrantlib import split_list
from discord.errors import NotFound
from datetime import datetime
from main import client_cls
from io import StringIO
from re import findall
from json import dumps
from time import time



class log_listeners(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.recently_deleted = []

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if not message.guild: return
		guild_data = await self.client.db.guilds.read(message.guild.id)
		if not guild_data['log_config']['enabled']: return
		if guild_data['log_config']['log_all_messages']: await self.log(message,'sent')
		regex = guild_data['regex']

		try: regex['channel'][str(message.channel.id)]
		except KeyError: regex['channel'][str(message.channel.id)] = []

		for expression in regex['guild']+regex['channel'][str(message.channel.id)]:
			if findall(expression,message.content):
				self.recently_deleted.append(message.id)
				await message.delete()

				if (
					not guild_data['log_config']['log_channel'] or
					not guild_data['log_config']['filtered_messages'] or
					guild_data['log_config']['log_bots'] and message.author.bot):
					await self.log(message)
					return
				
				embed = Embed(title=f'message filtered in {message.channel.name}',
				description=f'[jump to channel](<{message.channel.jump_url}>)\n[{str(message.author).lower()}\'s profile](<{message.author.jump_url}>)\n',
				color=0xffff69)
				embed.set_author(name=message.author.display_name,icon_url=message.author.display_avatar.url)
				embed.set_footer(text=f'message id: {message.id}\nuser id:    {message.author.id}')
				embed.add_field(name=f'DELETED <t:{int(message.created_at.timestamp())}:t>',value=(message.content if len(message.content) <= 1024 else f'{message.content[:1021]}...') or '​',inline=False)
				
				log_msg = await self.client.get_channel(guild_data['log_config']['log_channel']).send(embed=embed)
				await self.log(message,log_message=log_msg)

	@Cog.listener()
	async def on_message_edit(self,before:Message,after:Message) -> None:
		if not before.guild or before.content == after.content: return
		guild_data = await self.client.db.guilds.read(before.guild.id)
		if not guild_data['log_config']['enabled']: return
		
		regex = guild_data['regex']

		try: regex['channel'][str(after.channel.id)]
		except KeyError: regex['channel'][str(after.channel.id)] = []

		for expression in regex['guild']+regex['channel'][str(after.channel.id)]:
			if findall(expression,after.content):
				await after.delete()

		if (
			not guild_data['log_config']['log_channel'] or
			not guild_data['log_config']['edited_messages'] or
			guild_data['log_config']['log_bots'] and before.author.bot):
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
		
		log_msg = await self.client.get_channel(guild_data['log_config']['log_channel']).send(embed=embed)
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
		if not guild_data['log_config']['enabled']: return

		if (
			not guild_data['log_config']['log_channel'] or
			not guild_data['log_config']['deleted_messages'] or
			guild_data['log_config']['log_bots'] and message.author.bot):
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
		embed.add_field(name=f'DELETED <t:{int(deleted_at.timestamp())}:t>',value=(message.content if len(message.content) <= 1024 else f'{message.content[:1021]}...') or '​',inline=False)
		if message.attachments:
			
			embed.add_field(name='attachments',value='\n'.join([a.filename for a in message.attachments]),inline=False)

		log_msg = await self.client.get_channel(guild_data['log_config']['log_channel']).send(embed=embed)
		await self.log(message,deleted_at=deleted_at,log_message=log_msg)

	@Cog.listener()
	async def on_bulk_message_delete(self,messages:list[Message]) -> None:
		deleted_at = datetime.now()
		if not messages[0].guild: return
		guild_data = await self.client.db.guilds.read(messages[0].guild.id)
		if not guild_data['log_config']['enabled']: return

		if (
			not guild_data['log_config']['log_channel'] or
			not guild_data['log_config']['deleted_messages'] or
			guild_data['log_config']['log_bots'] and message[0].author.bot):
			for message in messages: await self.log(message)
			return
		
		embed = Embed(title=f'{len(messages)} messages were bulk deleted in {messages[0].channel.name}',
		description=f'[jump to channel](<{messages[0].channel.jump_url}>)\n',
		color=0xff6969)
		for chunk in split_list([str(m.id) for m in messages],48):
			embed.add_field(name=f'DELETED <t:{int(deleted_at.timestamp())}:t>',value='\n'.join(chunk))

		log_msg = await self.client.get_channel(guild_data['log_config']['log_channel']).send(embed=embed)
		for message in messages: await self.log(message,deleted_at=deleted_at,log_message=log_msg)

	@Cog.listener()
	async def on_member_join(self,member:Member) -> None:
		guild_data = await self.client.db.guilds.read(member.guild.id)

		if guild_data['log_config']['log_channel'] and guild_data['log_config']['member_join']:
			embed = Embed(
				title=f'{member.name} joined the server',
				description=f"""id: {member.id}
				username: {member.name}
				discriminator: {member.discriminator}""",
				color=0x69ff69)
			embed.set_thumbnail(url=member.display_avatar.with_size(512).with_format('png').url)
			await self.client.get_channel(guild_data['log_channel']).send(embed=embed)

	@Cog.listener()
	async def on_member_remove(self,member:Member) -> None:
		guild_data = await self.client.db.guilds.read(member.guild.id,['log_config'])
		
		if guild_data['log_channel'] and guild_data['member_leave']:
			embed = Embed(
				title=f'{member.name} left the server',
				description=f"""id: {member.id}
				username: {member.name}
				discriminator: {member.discriminator}""",
				color=0xff6969)
			embed.set_thumbnail(url=member.display_avatar.with_size(512).with_format('png').url)
			await self.client.get_channel(guild_data['log_channel']).send(embed=embed)

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

class log_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

	logging = SlashCommandGroup('logging','logging commands')

	async def build_embed(self,doc:dict) -> Embed:
		guild:Guild          = self.client.get_guild(doc['guild']) or await self.client.fetch_guild(doc['guild'])
		channel:TextChannel  = guild.get_channel(doc['channel']) or await guild.fetch_channel(doc['channel'])
		author:Member        = guild.get_member(doc['author']) or await guild.fetch_member(doc['author'])
		try: message:Message = self.client.get_message(doc['_id']) or await channel.fetch_message(doc['_id'])
		except NotFound: message = None
		if doc['reply_to']:
			try: replying_to:Message = self.client.get_message(doc['reply_to']) or await channel.fetch_message(doc['reply_to'])
			except NotFound: replying_to = None
		else: replying_to = None

		if None in [guild,author,channel]:
			return False

		match doc['logs'][-1][1]:
			case 'original': title = f'sent a message in {channel.name}'
			case 'edited': title = f'edited a message in {channel.name}'
			case 'deleted': title = f'deleted a message in {channel.name}'

		msg_jmp   = None if message     is None else f'[jump to message](<{message.jump_url}>)\n'
		reply_jmp = None if replying_to is None else f'[replying to {str(replying_to.author).lower()}](<{replying_to.jump_url}>)\n'

		embed = Embed(title=title,
		description=f'[jump to channel](<{channel.jump_url}>)\n{msg_jmp or ""}{reply_jmp or ""}[{str(author).lower()}\'s profile](<{author.jump_url}>)\n',
		color=0xff6969)
		embed.set_author(name=author.display_name,icon_url=author.display_avatar.url)
		embed.set_footer(text=f'message id: {doc["_id"]}\nuser id:    {author.id}')
		
		if len(doc['logs']) > 25:
			embed.description+='this message has more than 25 edits to see full history, use /logging get with <raw> set to true'
		for log in doc['logs'][:25]:
			embed.add_field(name=f'{log[1].upper()} <t:{log[0]}:t>',value=(log[2] if len(log[2]) <= 1024 else f'{log[2][:1021]}...') or '​',inline=False)

		match embed.fields[-1].name[0]:
			case 'O': embed.color = 0x69ff69
			case 'E': embed.color = 0xffff69
			case 'D': embed.color = 0xff6969
			case  _ : raise

		return embed

	@logging.command(name='set_channel',
		description='set logging channel',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True),
		options=[
			option(TextChannel,name='channel',description='channel to broadcast logs to')])
	async def slash_logging_set_channel(self,ctx:ApplicationContext,channel:TextChannel) -> None:
		await self.client.db.guilds.write(ctx.guild.id,['log_config','log_channel'],channel.id)
		await ctx.response.send_message('logging enabled',ephemeral=await self.client.hide(ctx))

	@logging.command(name='get',
		description='get logs from message by id',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True),
		options=[
			option(str,name='message_id',description='in the footer of logs'),
			option(bool,name='raw',description='show the raw, not pretty unformatted log',required=False,default=False)])
	async def slash_logging_get(self,ctx:ApplicationContext,message_id:str,raw:bool):
		log = await self.client.db.messages.read(int(message_id))
		if log is None or log['guild'] != ctx.guild.id:
			await ctx.response.send_message(f'invalid message id, try using the message command on either the original message or the log\nright click -> Apps -> message data',ephemeral=await self.client.hide(ctx))
			return
		if raw:
			response = dumps(log,indent=2)
			if len(response)+8 > 2000: await ctx.response.send_message('response too long. sent as file',file=File(StringIO(response),f'{message_id}.json'),ephemeral=await self.client.hide(ctx))
			else: await ctx.response.send_message(f'```\n{response}\n```',ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.send_message(embed=await self.build_embed(log),ephemeral=await self.client.hide(ctx))
	
	@logging.command(name='recent',
		description='get ten most recent logs',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True),
		options=[option(User,name='user',description='limit to logs from a specific user',required=False)])
	async def slash_logging_recent(self,ctx:ApplicationContext,user:User) -> None:
		search = {'guild':ctx.guild.id} if user is None else {'guild':ctx.guild.id,'author':user.id}
		data = [doc async for doc in self.client.db.messages.raw.find(search,sort=[('_id',-1)],limit=10)]

		if data == []:
			await ctx.response.send_message(f'no logs found',ephemeral=True)
			return

		await ctx.response.send_message(embeds=[await self.build_embed(doc) for doc in data],ephemeral=await self.client.hide(ctx))

	@logging.command(name='all',
		description='get a file with all log history. one use per day.',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True,manage_guild=True),
		options=[
			option(str,name='sorting',description='sorting order',choices=['newest first','oldest first'])])
	async def slash_logging_all(self,ctx:ApplicationContext,sorting:str) -> None:
		await ctx.defer(ephemeral=True)
		if time()-await self.client.db.guilds.read(ctx.guild.id,['last_history']) < 86400:
			await ctx.followup.send('you cannot use this command again until 24 hours have passed.',ephemeral=True)
			return

		data = [doc async for doc in self.client.db.messages.raw.find({'guild_id':ctx.guild.id},sort=[('_id',-1 if sorting == 'newest first' else 1)])]
		data.insert(0,f'total entries: {len(data)}')

		if data == []:
			await ctx.followup.send(f'no logs found',ephemeral=True)
			return

		await ctx.followup.send('all logs',file=File(StringIO(dumps(data,indent=2)),'history.json'),ephemeral=True)
		await self.client.db.guilds.write(ctx.guild.id,['last_history'],time())

	@message_command(
		name='message data',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True))
	async def message_get_by_id(self,ctx:ApplicationContext,message:Message) -> None:
		log = await self.client.db.messages.read(int(message.id))
		if log is None: log = await self.client.db.messages.raw.find_one({'log_message':message.id})
		if log is None or log['guild'] != ctx.guild.id:
			await ctx.response.send_message(f'invalid message id.',ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.send_message(embed=await self.build_embed(log),ephemeral=await self.client.hide(ctx))


def setup(client:client_cls) -> None:
	client.add_cog(log_listeners(client))
	client.add_cog(log_commands(client))	