from regex import sub,search,IGNORECASE,split,fullmatch
from discord.errors import Forbidden,HTTPException
from utils.tyrantlib import merge_dicts
from discord.ext.commands import Cog
from .shared import reload_guilds
from urllib.parse import quote
from main import client_cls
from discord import Message
from asyncio import sleep


class auto_response_listeners(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.base_responses = None
		self.guild_responses = {}

	@Cog.listener()
	async def on_connect(self) -> None:
		self.base_responses = await self.client.db.inf.read('auto_responses',['au'])
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
			await message.channel.send('https://cdn.tyrant.link/reg/nal/dm.png')
			return
		
		if message.content is None: return
		if reload_guilds:
			for i in reload_guilds:
				self.guild_responses.pop(i,None)
				try: reload_guilds.remove(i)
				except ValueError: pass
		if self.base_responses is None:
			self.base_responses = await self.client.db.inf.read('auto_responses',['au'])
			self.client.au = self.base_responses
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
				if await self.listener_dad_bot(message): return
			case 'whitelist' if message.channel.id in guild['db']['whitelist']:
				if await self.listener_dad_bot(message): return
			case 'blacklist' if message.channel.id not in guild['db']['blacklist']:
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
		responses = merge_dicts(self.base_responses,self.guild_responses[message.guild.id])
		try: check = self.au_check(responses,message.content[:-1] if message.content[-1] in ['.','?','!'] else message.content)
		except Exception: return False
		if check is None: return False

		data = responses[check[0]][check[1]]
		while redir:=data.get('redir',False):
			data = responses[check[0]][redir]
		
		if (response:=data.get('response',None)) is None: return False
		if data.get('nsfw',False) and not message.channel.nsfw: return False
		if (user_id:=data.get('user',None)) is not None and str(message.author.id) != user_id: return False
		if data.get('file',False): response = f'https://cdn.tyrant.link/reg/nal/auto_responses/{quote(response)}'

		try: await message.channel.send(response)
		except Forbidden: return False
		for delay,followup in data.get('followup',[]):
			await sleep(delay)
			await message.channel.send(followup)

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

		await self.client.log.listener(message,splitter=splitter)