from regex import sub,search,IGNORECASE,split,fullmatch
from discord.errors import Forbidden,HTTPException
from discord.ext.commands import Cog
from discord import Message,Thread
from urllib.parse import quote
from main import client_cls
from asyncio import sleep
from time import time


class auto_response_listeners(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.base_responses = None
		self.guild_responses = {}
		self.cooldowns = {'au':{},'db':{}}

	@Cog.listener()
	async def on_connect(self) -> None:
		self.base_responses = await self.client.db.inf.read('/reg/nal',['auto_responses'])
		self.client.au = self.base_responses

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
			await message.channel.send('https://regn.al/dm.png')
			return
		
		if message.content is None: return
		for i in self.client.flags:
			if i[0] != 'RELOAD_AU': continue
			for guild_id in i[1:]:
				print(f'reloading {guild_id}')
				self.guild_responses.pop(guild_id,None)
			self.client.flags.remove(i)
		if self.base_responses is None:
			self.base_responses = await self.client.db.inf.read('/reg/nal',['auto_responses'])
			self.client.au = self.base_responses
		if self.guild_responses.get(message.guild.id,None) is None:
			self.guild_responses[message.guild.id] = await self.client.db.guilds.read(message.guild.id,['data','auto_responses','custom'])

		channel = message.channel.parent if isinstance(message.channel,Thread) else message.channel
		if time()-self.cooldowns['au'].get(message.author.id if guild['config']['auto_responses']['cooldown_per_user'] else message.channel.id,0) > guild['config']['auto_responses']['cooldown']:
			match guild['config']['auto_responses']['enabled']:
				case 'enabled':
					if await self.listener_auto_response(message): return
				case 'whitelist' if channel.id in guild['data']['auto_responses']['whitelist']:
					if await self.listener_auto_response(message): return
				case 'blacklist' if channel.id not in guild['data']['auto_responses']['blacklist']:
					if await self.listener_auto_response(message): return
				case 'disabled': pass
		if time()-self.cooldowns['db'].get(message.author.id if guild['config']['auto_responses']['cooldown_per_user'] else message.channel.id,0) > guild['config']['dad_bot']['cooldown']:
			match guild['config']['dad_bot']['enabled']:
				case 'enabled':
					if await self.listener_dad_bot(message): return
				case 'whitelist' if channel.id in guild['data']['dad_bot']['whitelist']:
					if await self.listener_dad_bot(message): return
				case 'blacklist' if channel.id not in guild['data']['dad_bot']['blacklist']:
					if await self.listener_dad_bot(message): return
				case 'disabled': pass

	def au_check(self,responses,message:str) -> tuple[str,str]|None:
		for key,data in responses['exact'].items():
			if data.get('regex',False):
				if fullmatch(key,message.lower()):
					return ('exact',key)
				continue
			if message.lower() == key:
				return ('exact',message.lower())
		for key,data in responses['exact-cs'].items():
			if data.get('regex',False):
				if fullmatch(key,message):
					return ('exact-cs',key)
				continue
			if message == key:
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
		for responses in [self.guild_responses[message.guild.id],self.base_responses]:
			try: check = self.au_check(responses,message.content[:-1] if message.content[-1] in ['.','?','!'] else message.content)
			except Exception: continue
			if check is not None: break
		else: return False

		data:dict = responses[check[0]][check[1]]
		while redir:=data.get('redir',False):
			data = responses[check[0]][redir]
		
		if (response:=data.get('response','{none}')).lower() == '{none}': return False
		if data.get('nsfw',False) and not message.channel.nsfw: return False
		if (user_id:=data.get('user',None)) is not None and str(message.author.id) != user_id: return False
		if data.get('file',False): response = f'https://regn.al/au/{quote(response)}'

		try: await message.channel.send(response)
		except Forbidden: return False
		for delay,followup in data.get('followup',[]):
			await sleep(delay)
			await message.channel.send(followup)

		self.cooldowns['au'].update({message.author.id if await self.client.db.guilds.read(message.guild.id,['config','auto_responses','cooldown_per_user']) else message.channel.id:int(time())})
		await self.client.log.listener(message,category=check[0],trigger=check[1])
		return True

	async def listener_dad_bot(self,message:Message) -> None:
		response = ''
		input = sub(r"""<(@!|@|@&)\d{10,25}>|@everyone|@here|(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?""",'[REDACTED]',sub(r'\*|\_|\~|\`|\|','',message.content))
		for p_splitter in ["I'm",'im','I am','I will be',"I've",'ive']:
			s = search(p_splitter,input,IGNORECASE)

			if s == None: continue
			try:
				if s.span()[0] != 0:
					if input[s.span()[0]-1] != ' ': continue
				if input[s.span()[0]+(len(p_splitter))] != ' ': continue
			except IndexError: continue

			p_response = split(p_splitter,input,1,IGNORECASE)[1:]
			if len(response) < len(''.join(p_response)): response,splitter = ''.join(p_response),p_splitter

		if response == '': return

		try: await message.channel.send(f'hi{response}, {splitter} {message.guild.me.display_name if message.guild else self.client.user.name}')
		except Forbidden: return False
		except HTTPException: await message.channel.send(f'hi{response[:1936]} (character limit), {splitter} {message.guild.me.display_name if message.guild else self.client.user.name}')
		
		self.cooldowns['db'].update({message.author.id if await self.client.db.guilds.read(message.guild.id,['config','dad_bot','cooldown_per_user']) else message.channel.id:int(time())})
		await self.client.log.listener(message,splitter=splitter)