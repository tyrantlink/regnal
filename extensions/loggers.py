from discord import User,TextChannel,File,Message,ApplicationContext,Member,Permissions
from discord.commands import SlashCommandGroup,Option as option
from discord.ext.commands import Cog,message_command
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
				await self.log(message,'deleted',delreason=f'matched regex "{expression}"')

				if (
					not guild_data['log_config']['log_channel'] or
					not guild_data['log_config']['filtered_messages'] or
					guild_data['log_config']['log_bots'] and message.author.bot):
					return
				
				await self.client.get_channel(guild_data['log_config']['log_channel']).send(
					f'[{message.id}] "{message.content}" by {message.author} was filtered in {message.channel.mention}')

	@Cog.listener()
	async def on_message_edit(self,before:Message,after:Message) -> None:
		if not before.guild or before.content == after.content: return
		guild_data = await self.client.db.guilds.read(before.guild.id)
		if  not guild_data['log_config']['enabled']: return
		await self.log(before,'edited',after)
		
		regex = guild_data['regex']

		try: regex['channel'][str(after.channel.id)]
		except KeyError: regex['channel'][str(after.channel.id)] = []

		for expression in regex['guild']+regex['channel'][str(after.channel.id)]:
			if findall(expression,after.content):
				await after.delete()
				await self.log(after,'deleted',delreason=f'matched regex "{expression}"')

		if (
			not guild_data['log_config']['log_channel'] or
			not guild_data['log_config']['edited_messages'] or
			guild_data['log_config']['log_bots'] and before.author.bot):
			return
		
		response = f'[{before.id}] "{before.content}" was edited into "{after.content}" by {before.author} in {before.channel.mention}'
		await self.client.get_channel(guild_data['log_config']['log_channel']).send(
			response if len(response) < 2000 else f'[{before.id}] {before.author} edited a message. character limit reached, use /get_log by_id {before.id} to see full details')
	
	@Cog.listener()
	async def on_message_delete(self,message:Message) -> None:
		if message.id in self.recently_deleted:
			self.recently_deleted.remove(message.id)
			return
		if not message.guild: return

		guild_data = await self.client.db.guilds.read(message.guild.id)
		if not guild_data['log_config']['enabled']: return
		await self.log(message,'deleted')

		if (
			not guild_data['log_config']['log_channel'] or
			not guild_data['log_config']['deleted_messages'] or
			guild_data['log_config']['log_bots'] and message.author.bot):
			return

		attachments = f" [{', '.join([att.filename for att in message.attachments])}]" if message.attachments else ''
		content = f' "{message.content}"' if message.content else ''
		response = f'[{message.id}]{attachments}{content} by {message.author} was deleted in {message.channel.mention}'
		await self.client.get_channel(guild_data['log_config']['log_channel']).send(
			response if len(response) < 2000 else f'[{message.id}] {message.author} deleted a message. character limit reached, use /get_log by_id {message.id} to see full details')

	@Cog.listener()
	async def on_bulk_message_delete(self,messages:list[Message]) -> None:
		if not messages[0].guild: return
		guild_data = await self.client.db.guilds.read(messages[0].guild.id)
		if not guild_data['log_config']['enabled']: return
		for message in messages: await self.log(message,'deleted')

		if (
			not guild_data['log_config']['log_channel'] or
			not guild_data['log_config']['deleted_messages'] or
			guild_data['log_config']['log_bots'] and message.author.bot):
			return
		
		message_ids = [f'[{m.id}]' for m in messages]
		await self.client.get_channel(guild_data['log_config']['log_channel']).send(
			f'{len(messages)} messages were bulk deleted in {messages[0].channel.mention}\n{" ".join(message_ids)}')

	@Cog.listener()
	async def on_member_join(self,member:Member) -> None:
		guild_data = await self.client.db.guilds.read(member.guild.id)

		if guild_data['log_config']['log_channel'] and guild_data['log_config']['member_join']:
			await self.client.get_channel(guild_data['log_config']['log_channel']).send(
				f'[{member.id}] {member} joined the server.')

	@Cog.listener()
	async def on_member_remove(self,member:Member) -> None:
		guild_data = await self.client.db.guilds.read(member.guild.id,['log_config'])
		
		if guild_data['log_channel'] and guild_data['member_leave']:
			await self.client.get_channel(guild_data['log_channel']).send(
				f'[{member.id}] {member} left the server.')

	async def log(self,message:Message,type:str,after_message:Message=None,delreason:str='deleted by a user') -> None:
		if message.author == self.client.user: return
		response = await self.client.db.messages.read(message.id)

		if response == None:
			response = {
				'_id':message.id,
				'guild_id':message.guild.id,
				'channel_id':message.channel.id,
				'author_id':message.author.id,
				'bot':message.author.bot,
				'status':type,
				'content':{
					str(datetime.timestamp(message.created_at)):{
						'type':type,
						'content':message.content}},
				'tts':message.tts,
				'mention_everyone':message.mention_everyone,
				'attachments':[attachment.filename for attachment in message.attachments],
				'referenced_message_id':message.reference.message_id if message.reference else None}
			match type:
				case 'sent':
					pass
				case 'edited':
					response['content'][str(datetime.timestamp(after_message.edited_at))[:-3]] = {'type':'edit','content':after_message.content}
				case 'deleted':
					response['content'][str(round(time(),3))] = {'type':'delete','content':message.content}
			await self.client.db.messages.new(message.id,response)
		else:
			match type:
				case 'sent':
					print('message pushed through log while already being logged')
				case 'edited':
					await self.client.db.messages.write(message.id,['content',str(datetime.timestamp(after_message.edited_at))[:-3]],{'type':'edit','content':after_message.content})
				case 'deleted':
					await self.client.db.messages.write(message.id,['content',str(round(time(),3))],{'type':'delete','content':message.content,'reason':delreason})
			
			if response['status'] != type:
				await self.client.db.messages.write(message.id,['status'],type)

class log_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client
	
	get_log = SlashCommandGroup('get_log','get log information')

	async def base_get_by_id(self,message_id:str|int,guild_id:str|int) -> str:
		try: message_id = int(message_id)
		except: return 'invalid message id'
		message_data = await self.client.db.messages.read(message_id)
		if message_data == None or message_data['guild_id'] != guild_id:
			return 'invalid message id'

		return dumps(message_data,indent=2)

	@get_log.command(name='set_channel',
		description='set logging channel',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True),
		options=[option(TextChannel,name='channel',description='channel to broadcast logs to')])
	async def slash_get_log_set_channel(self,ctx:ApplicationContext,channel:TextChannel) -> None:
		await self.client.db.guilds.write(ctx.guild.id,['log_config','log_channel'],channel.id)
		await ctx.response.send_message('logging enabled',ephemeral=True)

	@get_log.command(name='by_id',
		description='get message details by id',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True),
		options=[
			option(str,name='message_id',description='id of message')])
	async def slash_get_by_id(self,ctx:ApplicationContext,message_id:str|int) -> None:
		response = await self.base_get_by_id(message_id,ctx.guild.id)
		if len(response)+8 > 2000: await ctx.response.send_message('response too long. sent as file',file=File(StringIO(response),f'{message_id}.json'),ephemeral=True)
		else: await ctx.response.send_message(f'```\n{response}\n```',ephemeral=True)

	@get_log.command(name='recent_from',
		description='get ten most recent logs from a user.',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True),
		options=[
			option(User,name='user',description='user'),
			option(str,name='status',description='message type',choices=['sent','edited','deleted'])])
	async def slash_get_recent_from(self,ctx:ApplicationContext,user:User|Member,status:str) -> None:
		data = [doc async for doc in self.client.db.messages.raw.find({'guild_id':ctx.guild.id,'author_id':user.id,'status':status},sort=[('_id',-1)],limit=10)]
		if data == []:
			await ctx.response.send_message(f'no logs found from user {user} with status {status}',ephemeral=True)
			return

		await ctx.response.send_message(f'logs for user {user} with status {status}',file=File(StringIO(dumps(data,indent=2)),filename='logs.json'),ephemeral=True)
	
	@get_log.command(name='recent',
		description='get ten most recent logs',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True),)
	async def slash_get_recent(self,ctx:ApplicationContext) -> None:
		data = [doc async for doc in self.client.db.messages.raw.find({'guild_id':ctx.guild.id},sort=[('_id',-1)],limit=10)]

		if data == []:
			await ctx.response.send_message(f'no logs found',ephemeral=True)
			return

		await ctx.response.send_message('recent logs',file=File(StringIO(dumps(data,indent=2)),'logs.json'),ephemeral=True)

	@get_log.command(name='history',
		description='get a file with all log history. one use per day.',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True,manage_guild=True),
		options=[
			option(str,name='sorting',description='sorting order',choices=['newest first','oldest first'])])
	async def slash_get_history(self,ctx:ApplicationContext,sorting:str) -> None:
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
		response = await self.base_get_by_id(message.id,ctx.guild.id)
		if len(response)+8 > 2000: await ctx.response.send_message('response too long. sent as file',file=File(StringIO(response),filename=f'{message.id}.json'),ephemeral=True)
		else: await ctx.response.send_message(f'```\n{response}\n```',ephemeral=True)


def setup(client:client_cls) -> None:
	client.add_cog(log_listeners(client))
	client.add_cog(log_commands(client))	