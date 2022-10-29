from discord import Message,ApplicationContext,Embed,Permissions,Member,Interaction,InputTextStyle
from discord.ui import Modal,InputText
from discord.commands import slash_command,Option as option
from re import sub,search,IGNORECASE,split
from utils.tyrantlib import merge_dicts
from discord.errors import Forbidden,HTTPException
from discord.ext.commands import Cog
from main import client_cls
from asyncio import sleep

c_au_choices = {
	'trigger anywhere within message':'contains',
	'message is exactly trigger (case insensitive)':'exact',
	'message is exactly trigger (case sensitive)':'exact-cs'}
reload_guilds = []

class input_text(Modal):
	def __init__(self,client:client_cls,guild_id:int,title:str,items:list[InputText],method:str,user:Member=None) -> None:
		self.client   = client
		self.guild_id = guild_id
		self.method   = method
		self.user     = user
		super().__init__(title=title)
		for i in items: self.add_item(i)

	async def callback(self,interaction:Interaction) -> None:
		custom = await self.client.db.guilds.read(self.guild_id,['au','custom',self.method])
		trigger = (self.children[0].value if self.method == 'exact-cs' else self.children[0].value.lower()).strip()
		match len(self.children):
			case 1: # means is delete
				if trigger not in custom.keys():
					await interaction.response.send_message(f'> {trigger}\nnot found in custom auto responses!',ephemeral=True)
					return
				await self.client.db.guilds.unset(self.guild_id,['au','custom'],trigger)
			case 2: # means is add
				if trigger in custom.keys():
					await interaction.response.send_message(f'> {trigger}\nis already in the auto responses:',ephemeral=True)
					return
				au = {'response':self.children[1].value,}
				if self.user is not None: au.update({'user':str(self.user.id)})
				await self.client.db.guilds.write(self.guild_id,['au','custom',self.method,trigger],au)
				await interaction.response.send_message(f'> {trigger}\nsuccessfully added to auto responses',ephemeral=True)
			case _: raise
		reload_guilds.append(self.guild_id)

class auto_responses_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client
		self.responses = None
		self.guild_responses = {}

	@Cog.listener()
	async def on_connect(self):
		self.responses = await self.client.db.inf.read('auto_responses',['au'])

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if message.guild:
			try: guild = await self.client.db.guilds.read(message.guild.id)
			except: guild = await self.client.db.guilds.read(0)
		else: guild = await self.client.db.guilds.read(0)
		if guild is None: return

		try:
			if (
				message.author.bot or
				message.author == self.client.user or 
				await self.client.db.users.read(message.author.id,['config','ignored'])):
					return
		except: return

		if message.guild is None:
			await message.channel.send('https://cdn.tyrant.link/reg/nal/dm.png')
			return
		
		if message.content is None: return

		for i in reload_guilds:
			self.guild_responses.pop(i)
		if self.responses is None:
			self.responses = await self.client.db.inf.read('auto_responses',['au'])
		if self.guild_responses.get(message.guild.id,None) is None:
			self.guild_responses[message.guild.id] = await self.client.db.guilds.read(message.guild.id,['au','custom'])

		match guild['config']['auto_responses']:
			case 'enabled':
				if await self.listener_auto_response(message): return
			case 'whitelist' if message.channel.id in guild['au']['whitelist']:
				if await self.listener_auto_response(message): return
			case 'blacklist' if message.channel.id not in guild['au']['blacklist']:
				if await self.listener_auto_response(message): return
			case 'disabled': pass
		match guild['config']['dad_bot']:
			case 'enabled':
				if await self.listener_auto_response(message): return
			case 'whitelist' if message.channel.id in guild['db']['whitelist']:
				if await self.listener_auto_response(message): return
			case 'blacklist' if message.channel.id not in guild['db']['blacklist']:
				if await self.listener_auto_response(message): return
			case 'disabled': pass
		if guild['config']['dad_bot']: await self.listener_dad_bot(message)
	
	def au_check(self,responses,message:str) -> tuple[str,str]|None:
		if message.lower() in responses['exact']:
			return ('exact',message.lower())
		if message in responses['exact-cs']:
			return ('exact-cs',message)
		for i in responses['contains']:
			s = search(i,message.lower(),IGNORECASE)
			if s is None: continue
			try:
				if s.span()[0] != 0:
					if message.lower()[s.span()[0]-1] != ' ': continue
				if message.lower()[s.span()[0]+(len(i))] != ' ': continue
			except IndexError: pass
			return ('contains',i)

	async def listener_auto_response(self,message:Message) -> None:
		responses = merge_dicts(self.responses,self.guild_responses[message.guild.id])
		try: check = self.au_check(responses,message.content[:-1] if message.content[-1] in ['.','?','!'] else message.content)
		except Exception: return False
		if check is None: return False

		data = responses[check[0]][check[1]]
		while redir:=data.get('redir',False):
			data = responses[check[0]][redir]
		
		if (response:=data.get('response',None)) is None: return False
		if (user_id:=data.get('user',None)) is not None and str(message.author.id) != user_id: return False
		if data.get('file',False): response = f'https://cdn.tyrant.link/reg/nal/auto_responses/{response}'

		try: await message.channel.send(response)
		except Forbidden: return False
		for delay,followup in data.get('followup',[]):
			await sleep(delay)
			await message.channel.send(followup)

		await self.client.log.listener(message)
		return True

	async def listener_dad_bot(self,message:Message) -> None:
		response = ''
		input = sub(r'<(@!|@|@&)\d{10,25}>|@everyone|@here','[REDACTED]',sub(r'\*|\_|\~|\`|\|','',message.content))
		for p_splitter in ["I'm",'im','I am','I will be']:
			s = search(p_splitter,input,IGNORECASE)

			if s == None: continue
			try:
				if s.span()[0] != 0:
					if input[s.span()[0]-1] != ' ': continue
				if input[s.span()[0]+(len(p_splitter))] != ' ': continue
			except IndexError: return

			p_response = split(p_splitter,input,1,IGNORECASE)[1:]
			if len(response) < len(''.join(p_response)): response,splitter = ''.join(p_response),p_splitter

		if response == '': return

		try: await message.channel.send(f'hi{response}, {splitter} {message.guild.me.display_name if message.guild else self.client.user.name}')
		except Forbidden: return False
		except HTTPException: await message.channel.send(f'hi{response[:1936]} (character limit), {splitter} {message.guild.me.display_name if message.guild else self.client.user.name}')

		await self.client.log.listener(message)

	@slash_command(
		name='auto_response',
		description='add the current channel to the whitelist or blacklist',
		guild_only=True,default_member_permissions=Permissions(manage_channels=True),
		options=[option(str,name='option',description='auto_response commands',choices=['add','remove','list'])])
	async def slash_auto_response(self,ctx:ApplicationContext,option:str):
		au_cfg = await self.client.db.guilds.read(ctx.guild.id,['config','auto_responses'])
		match option:
			case 'add'|'remove':
				match au_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'auto responses are currently {au_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						if option == 'add': await self.client.db.guilds.append(ctx.guild.id,['au',au_cfg],ctx.channel.id)
						else              : await self.client.db.guilds.remove(ctx.guild.id,['au',au_cfg],ctx.channel.id)
						await ctx.response.send_message(f'successfully added <#{ctx.channel.id}> to the {au_cfg}.',ephemeral=await self.client.hide(ctx))
					case _: raise
			case 'list':
				match au_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'auto responses are currently {au_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						await ctx.response.send_message(embed=Embed(title=au_cfg,description='\n'.join(await self.client.db.guilds.read(ctx.guild.id,['au',au_cfg]))),ephemeral=await self.client.hide(ctx))
					case _: raise
			case _: raise
	
	@slash_command(
		name='dad_bot',
		description='add the current channel to the whitelist or blacklist',
		guild_only=True,default_member_permissions=Permissions(manage_channels=True),
		options=[option(str,name='option',description='dad_bot commands',choices=['add','remove','list'])])
	async def slash_auto_response(self,ctx:ApplicationContext,option:str):
		db_cfg = await self.client.db.guilds.read(ctx.guild.id,['config','dad_bot'])
		match option:
			case 'add'|'remove':
				match db_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'dad bot is currently {db_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						if option == 'add': await self.client.db.guilds.append(ctx.guild.id,['db',db_cfg],ctx.channel.id)
						else              : await self.client.db.guilds.remove(ctx.guild.id,['db',db_cfg],ctx.channel.id)
						await ctx.response.send_message(f'successfully added <#{ctx.channel.id}> to the {db_cfg}.',ephemeral=await self.client.hide(ctx))
					case _: raise
			case 'list':
				match db_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'dad bot is currently {db_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						await ctx.response.send_message(embed=Embed(title=db_cfg,description='\n'.join(await self.client.db.guilds.read(ctx.guild.id,['db',db_cfg]))),ephemeral=await self.client.hide(ctx))
					case _: raise
			case _: raise

	@slash_command(
		name='custom_auto_response',
		description='add or remove custom auto responses',
		guild_only=True,default_member_permissions=Permissions(manage_messages=True),
		options=[
			option(str,name='action',description='add, remove, or list custom auto responses',choices=['add','remove','list']),
			option(str,name='method',description='when the auto response is triggered',required=False,default='message is exactly trigger (case insensitive)',choices=list(c_au_choices.keys())),
			option(Member,name='user',description='limit response to specific user',required=False)])
	async def slash_custom_auto_response(self,ctx:ApplicationContext,action:str,method:str,user:Member):
		custom_au = await self.client.db.guilds.read(ctx.guild.id,['au','custom'])
		au_length = sum([len(i) for i in custom_au.values()])
		match action:
			case 'add':
				if au_length >= 50:
					await ctx.response.send_message('a single server can\'t have more than 25 custom auto responses!',ephemeral=await self.client.hide(ctx))
					return
				await ctx.response.send_modal(
					input_text(self.client,ctx.guild.id,
						'add an auto response',[
							InputText(label='trigger message',min_length=1,max_length=100,style=InputTextStyle.short),
							InputText(label='response',min_length=1,max_length=500,style=InputTextStyle.long)],
						c_au_choices.get(method,'error'),user))
			case 'remove':
				if au_length == 0:
					await ctx.response.send_message('there are no custom auto responses in this server!',ephemeral=await self.client.hide(ctx))
					return
				await ctx.response.send_modal(
					input_text(self.client,ctx.guild.id,
						'remove an auto response',[
							InputText(label='trigger message',min_length=1,max_length=100,style=InputTextStyle.short)],c_au_choices.get(method,'error')))
			case 'list':
				embed = Embed(title='custom auto responses',color=await self.client.embed_color(ctx))
				if au_length == 0: embed.description = 'no custom auto responses have been set'
				for trigger,data in custom_au.items():
					value = [f'response:\n{data.get("response","no response")}']
					user_id = data.get("user",None)
					if user_id is not None:
						value.insert(0,f'limited to user: {ctx.guild.get_member(user_id) or await ctx.guild.fetch_member(user_id)}')
					embed.add_field(name=trigger,value='\n'.join(value))
				await ctx.response.send_message(embed=embed)
			case _: raise


def setup(client:client_cls) -> None: client.add_cog(auto_responses_cog(client))