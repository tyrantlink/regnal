from discord.commands import SlashCommandGroup,Option as option
from discord.ext.commands import Cog,message_command
from discord import Embed,User,TextChannel,File
from discord.utils import escape_markdown
from utils.tyrantlib import has_perm
from datetime import datetime
from io import StringIO
from re import findall
from json import dumps
from time import time

class log_listeners(Cog):
	def __init__(self,client):
		self.client = client
		self.recently_deleted = []

	@Cog.listener()
	async def on_message(self,message):
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
	async def on_message_edit(self,before,after):
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
	async def on_message_delete(self,message):
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
	async def on_bulk_message_delete(self,messages):
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
	async def on_member_join(self,member):
		guild_data = await self.client.db.guilds.read(member.guild.id)

		if guild_data['log_config']['log_channel'] and guild_data['log_config']['member_join']:
			await self.client.get_channel(guild_data['log_config']['log_channel']).send(
				f'[{member.id}] {member} joined the server.')

	@Cog.listener()
	async def on_member_remove(self,member):
		guild_data = await self.client.db.guilds.read(member.guild.id)

		if guild_data['log_config']['log_channel'] and guild_data['log_config']['member_leave']:
			await self.client.get_channel(guild_data['log_config']['log_channel']).send(
				f'[{member.id}] {member} left the server.')
	
	async def log(self,message,type,after_message=None,delreason='deleted by a user'):
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
	def __init__(self,client):
		self.client = client
	
	get_log = SlashCommandGroup('get_log','get log information')
	regex = SlashCommandGroup('regex','configure regex filtering')
	regex_guild = regex.create_subgroup('guild','guild regex filters')
	regex_channel = regex.create_subgroup('channel','channel regex filters')

	async def base_get_by_id(self,message_id,guild_id):
		try: message_id = int(message_id)
		except: return 'invalid message id'
		message_data = await self.client.db.messages.read(message_id)
		if message_data == None or len(str(message_id)) != 18 or message_data['guild_id'] != guild_id:
			return 'invalid message id'

		return dumps(message_data,indent=2)

	@get_log.command(name='set_channel',
		description='set logging channel',
		options=[option(TextChannel,name='channel',description='channel to broadcast logs to')])
	@has_perm('administrator')
	async def slash_get_log_set_channel(self,ctx,channel):
		await self.client.db.guilds.write(ctx.guild.id,['log_config','log_channel'],channel.id)
		await ctx.response.send_message('logging enabled',required=False)

	@get_log.command(name='by_id',
		description='get message details by id',
		options=[
			option(str,name='message_id',description='id of message, 18 digits long.')])
	@has_perm('view_audit_log')
	async def slash_get_by_id(self,ctx,message_id):
		await ctx.defer(ephemeral=True)
		response = await self.base_get_by_id(message_id,ctx.guild.id)
		if len(response)+8 > 2000: await ctx.response.send_message('response too long. sent as file',file=File(StringIO(response),f'{message_id}.json'),ephemeral=True)
		else: await ctx.response.send_message(f'```\n{response}\n```',required=False)

	@get_log.command(name='recent_from',
		description='get ten most recent logs from a user.',
		options=[
			option(User,name='user',description='user'),
			option(str,name='status',description='message type',choices=['sent','edited','deleted'])])
	@has_perm('view_audit_log')
	async def slash_get_recent_from(self,ctx,user,status):
		await ctx.defer(ephemeral=True)
		data = [doc async for doc in self.client.db.messages.raw.find({'guild_id':ctx.guild.id,'author_id':user.id,'status':status},sort=[('_id',-1)],limit=10)]
		if data == []:
			await ctx.response.send_message(f'no logs found from user {user} with status {status}',ephemeral=True)
			return

		await ctx.response.send_message(f'logs for user {user} with status {status}',file=File(StringIO(dumps(data,indent=2)),filename='logs.json'),ephemeral=True)
	
	@get_log.command(name='recent',
		description='get ten most recent logs')
	@has_perm('view_audit_log')
	async def slash_get_recent(self,ctx):
		await ctx.defer(ephemeral=True)
		data = [doc async for doc in self.client.db.messages.raw.find({'guild_id':ctx.guild.id},sort=[('_id',-1)],limit=10)]

		if data == []:
			await ctx.response.send_message(f'no logs found',ephemeral=True)
			return

		await ctx.response.send_message('recent logs',file=File(StringIO(dumps(data,indent=2)),'logs.json'),ephemeral=True)

	@get_log.command(name='history',
		description='get a file with all log history. one use per day.',
		options=[
			option(str,name='sorting',description='sorting order',choices=['newest first','oldest first'])])
	@has_perm('view_audit_log')
	async def slash_get_history(self,ctx,sorting):
		await ctx.defer(ephemeral=True)
		if time()-await self.client.db.guilds.read(ctx.guild.id,['last_history']) < 86400:
			await ctx.response.send_message('you cannot use this command again until 24 hours have passed.',ephemeral=True)
			return

		data = [doc async for doc in self.client.db.messages.raw.find({'guild_id':ctx.guild.id},sort=[('_id',-1 if sorting == 'newest first' else 1)])]
		data.insert(0,f'total entries: {len(data)}')

		if data == []:
			await ctx.response.send_message(f'no logs found',ephemeral=True)
			return

		await ctx.response.send_message('all logs',file=File(StringIO(dumps(data,indent=2)),'history.json'),ephemeral=True)
		await self.client.db.guilds.write(ctx.guild.id,['last_history'],time())

	@regex_guild.command(name='list',
		description='list current guild-wide filters')
	@has_perm('manage_messages')
	async def slash_regex_guild_list(self,ctx):
		res = await self.client.db.guilds.read(ctx.guild.id,['regex','guild'])
		await ctx.response.send_message(embed=Embed(title='current guild filters regex' if res else 'no guild regex filters set',description=escape_markdown('\n'.join(res))),ephemeral=True)

	@regex_channel.command(name='list',
		description='list current channel filters',
		options=[
			option(TextChannel,name='channel',description='channel')])
	@has_perm('manage_messages')
	async def slash_regex_channel_list(self,ctx,channel):
		try: res = await self.client.db.guilds.read(ctx.guild.id,['regex','channel',channel])
		except: res = []
		await ctx.response.send_message(embed=Embed(title=f'{channel.mention} regex filters' if res else 'no channel regex filters set',description=escape_markdown('\n'.join(res))),ephemeral=True)

	@regex_guild.command(name='add',
		description='add guild-wide message filters',
		option=[
			option(str,name='filter',description='regex filter')])
	@has_perm('manage_messages')
	async def slash_regex_guild_add(self,ctx,filter):
		await self.client.db.guilds.append(ctx.guild.id,['regex','guild'],filter)
		await ctx.response.send_message(f'successfully added {escape_markdown(filter)} to the guild filter list.',ephemeral=True)

	@regex_channel.command(name='add',
		description='add channel specific message filters',
		option=[
			option(TextChannel,name='channel',description='channel'),
			option(str,name='filter',description='regex filter')])
	@has_perm('manage_messages')
	async def slash_regex_channel_add(self,ctx,channel,filter):
		await self.client.db.guilds.append(ctx.guild.id,['regex','channel',str(channel.id)],filter)
		await ctx.response.send_message(f'successfully added {escape_markdown(filter)} to the {channel.mention} filter list.',ephemeral=True)

	@regex_guild.command(name='remove',
		description='remove guild-wide message filters',
		option=[
			option(str,name='filter',description='regex filter')])
	@has_perm('manage_messages')
	async def slash_regex_guild_remove(self,ctx,filter):
		await self.client.db.guilds.remove(ctx.guild.id,['regex','guild'],filter)
		await ctx.response.send_message(f'successfully removed {escape_markdown(filter)} from the guild filter list.',ephemeral=True)

	@regex_channel.command(name='remove',
		description='remove channel specific message filters',
		option=[
			option(TextChannel,name='channel',description='channel'),
			option(str,name='filter',description='regex filter')])
	@has_perm('manage_messages')
	async def slash_regex_channel_remove(self,ctx,channel,filter):
		await self.client.db.guilds.remove(ctx.guild.id,['regex','channel',str(channel.id)],filter)
		await ctx.response.send_message(f'successfully removed {escape_markdown(filter)} from the {channel.mention} filter list.',ephemeral=True)


	@message_command(name='message data')
	async def message_get_by_id(self,ctx,message):
		await ctx.defer(ephemeral=True)
		response = await self.base_get_by_id(message.id,ctx.guild.id)
		if len(response)+8 > 2000: await ctx.response.send_message('response too long. sent as file',file=File(StringIO(response),filename=f'{message.id}.json'),ephemeral=True)
		else: await ctx.response.send_message(f'```\n{response}\n```',ephemeral=True)


def setup(client):
	client.add_cog(log_listeners(client))
	client.add_cog(log_commands(client))	