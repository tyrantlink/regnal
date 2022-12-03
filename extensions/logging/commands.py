from discord import User,TextChannel,File,Message,ApplicationContext,Member,Permissions,Embed,Guild
from discord.commands import SlashCommandGroup,Option as option
from discord.ext.commands import Cog,message_command
from discord.errors import NotFound
from main import client_cls
from io import StringIO
from json import dumps
from time import time


class logging_commands(Cog):
	def __init__(self,client:client_cls) -> None:
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
			embed.add_field(name=f'{"{:<9}".format(log[1].upper())} <t:{log[0]}:t>',value=(log[2] if len(log[2]) <= 1024 else f'{log[2][:1021]}...') or '​',inline=False)

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
		if time()-await self.client.db.guilds.read(ctx.guild.id,['data','last_history']) < 86400:
			await ctx.followup.send('you cannot use this command again until 24 hours have passed.',ephemeral=True)
			return

		data = [doc async for doc in self.client.db.messages.raw.find({'guild_id':ctx.guild.id},sort=[('_id',-1 if sorting == 'newest first' else 1)])]
		data.insert(0,f'total entries: {len(data)}')

		if data == []:
			await ctx.followup.send(f'no logs found',ephemeral=True)
			return

		await ctx.followup.send('all logs',file=File(StringIO(dumps(data,indent=2)),'history.json'),ephemeral=True)
		await self.client.db.guilds.write(ctx.guild.id,['data','last_history'],time())

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
