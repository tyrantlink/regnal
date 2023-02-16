from regex import sub,search,split,fullmatch,IGNORECASE
from discord.errors import Forbidden,HTTPException
from asyncio import sleep,create_task
from discord.ext.commands import Cog
from client import Client,MixedUser
from discord import Message,Thread
from urllib.parse import quote
from random import choices
from time import time


class AutoResponse:
	def __init__(self,trigger:str,**kwargs) -> None:
		self.trigger:str  = trigger
		self.response:str = kwargs.get('response',None)
		self.redir:str    = kwargs.get('redir',None)
		self.regex:bool   = kwargs.get('regex',False)
		self.nsfw:bool    = kwargs.get('nsfw',False)
		self.file:bool    = kwargs.get('file',False)
		self.user:str     = kwargs.get('user',None)
		self.guild:str    = kwargs.get('guild',None)
		self.followups:list[tuple[float,str]] = kwargs.get('followups',[])

class auto_response_listeners(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.base_responses = None
		self.guild_responses = {}
		self.cooldowns = {'au':{},'db':{}}
		self.timeouts = []

	@Cog.listener()
	async def on_connect(self) -> None:
		self.client.au = await self.client.db.inf('/reg/nal').auto_responses.read()
		self.base_responses = {
			'contains':self.load_au(self.client.au.get('contains',{})),
			'exact':self.load_au(self.client.au.get('exact',{})),
			'exact_cs':self.load_au(self.client.au.get('exact_cs',{}))}

	async def timeout(self,message_id:int) -> None:
		self.timeouts.append(message_id)
		await sleep(5)
		try: self.timeouts.remove(message_id)
		except ValueError: pass

	def load_au(self,au_dict:dict) -> dict[str,AutoResponse]:
		return {k:AutoResponse(k,
			response  = v.get('response',None),
			redir     = v.get('redir',None),
			regex     = v.get('regex',None),
			nsfw      = v.get('nsfw',False),
			file      = v.get('file',False),
			user      = v.get('user',None),
			guild     = v.get('guild',None),
			followups = v.get('followups',[])
		) for k,v in au_dict.items()}

	@Cog.listener()
	async def on_message(self,message:Message,user:MixedUser=None) -> None:
		if message is None or message.author.id == self.client.user.id: return
		# ignore webhooks except pk
		if message.webhook_id is not None and user is None: return
		create_task(self.timeout(message.id))

		if message.guild:
			try: guild = await self.client.db.guild(message.guild.id).read()
			except: guild = await self.client.db.guild(0).read()
		else: guild = await self.client.db.guild(0).read()
		if guild is None: return

		if guild.get('config',{}).get('general',{}).get('pluralkit',False) and user is None:
			if (pk:=await self.client.pk.get_message(message.id)):
				if pk is not None and pk.original == message.id:
					await self.on_message(self.client.get_message(pk.id),MixedUser('pluralkit',message.author,
						id=pk.member.uuid,
						bot=False))
					return
		if user is None: user = message.author

		try:
			if (
				user.bot or
				await self.client.db.user(user.id).config.general.ignored.read()):
					return
		except: return

		if message.guild is None:
			await message.channel.send('https://regn.al/dm.png')
			return

		if message.content is None: return
		if (reload:=self.client.flags.pop('RELOAD_AU',None)) is not None:
			for guild_id in reload:
				if guild_id == 'base': self.base_responses = None
				self.guild_responses.pop(guild_id,None)
		if self.base_responses is None: await self.on_connect()
		if self.guild_responses.get(message.guild.id,None) is None:
			guild_au = await self.client.db.guild(message.guild.id).data.auto_responses.custom.read()
			self.guild_responses[message.guild.id] = {
				'contains':self.load_au(guild_au.get('contains',{})),
				'exact':self.load_au(guild_au.get('exact',{})),
				'exact_cs':self.load_au(guild_au.get('exact_cs',{}))}

		channel = message.channel.parent if isinstance(message.channel,Thread) else message.channel
		if time()-self.cooldowns['au'].get(message.author.id if guild['config']['auto_responses']['cooldown_per_user'] else message.channel.id,0) > guild['config']['auto_responses']['cooldown']:
			match guild['config']['auto_responses']['enabled']:
				case 'enabled':
					if await self.listener_auto_response(message,user): return
				case 'whitelist' if channel.id in guild['data']['auto_responses']['whitelist']:
					if await self.listener_auto_response(message,user): return
				case 'blacklist' if channel.id not in guild['data']['auto_responses']['blacklist']:
					if await self.listener_auto_response(message,user): return
				case 'disabled': pass
		if time()-self.cooldowns['db'].get(message.author.id if guild['config']['auto_responses']['cooldown_per_user'] else message.channel.id,0) > guild['config']['dad_bot']['cooldown']:
			match guild['config']['dad_bot']['enabled']:
				case 'enabled':
					if await self.listener_dad_bot(message,user): return
				case 'whitelist' if channel.id in guild['data']['dad_bot']['whitelist']:
					if await self.listener_dad_bot(message,user): return
				case 'blacklist' if channel.id not in guild['data']['dad_bot']['blacklist']:
					if await self.listener_dad_bot(message,user): return
				case 'disabled': pass

	def au_check(self,responses:dict,message:str) -> tuple[str,str]|None:
		for trigger,au in responses['exact'].items():
			if au.regex:
				if fullmatch(trigger,message.lower()):
					return ('exact',trigger)
				continue
			if message.lower() == trigger:
				return ('exact',trigger)
		for trigger,au in responses['exact_cs'].items():
			if au.regex:
				if fullmatch(trigger,message):
					return ('exact_cs',trigger)
				continue
			if message == trigger:
				return ('exact_cs',trigger)
		for au in responses['contains']:
			s = search(au,message.lower(),IGNORECASE)
			if s is None: continue
			try:
				if s.span()[0] != 0:
					if message.lower()[s.span()[0]-1] != ' ': continue
				if message.lower()[s.span()[0]+(len(au))] != ' ': continue
			except IndexError: pass
			return ('contains',au)
		return (None,None)

	async def listener_auto_response(self,message:Message,user:MixedUser) -> None:
		content = message.content[:-9] if (delete_original:=message.content.endswith(' --delete')) else message.content
		for responses in [self.guild_responses[message.guild.id],self.base_responses]:
			try: mode,raw_au = self.au_check(responses,content[:-1] if content[-1] in ['.','?','!'] else content)
			except Exception: continue
			if mode is not None: break
		else: return False
		au:AutoResponse = responses[mode][raw_au]
		for i in range(10):
			if redir:=au.redir:
				au = responses[mode][redir]
			else: break
		else: return False

		if (response:=au.response) is None or response.lower() == '{none}': return False
		if au.nsfw and not message.channel.nsfw: return False
		if au.user is not None and str(message.author.id) != au.user: return False
		if au.guild is not None and str(message.guild.id) != au.guild: return False
		if au.file: response = f'https://regn.al/au/{quote(response)}'

		if message.id not in self.timeouts: return False
		try: await message.channel.send(response)
		except Forbidden: return False
		if delete_original and (content.lower() == raw_au or au.regex) and au.file: await message.delete(reason='auto response deletion')
		for delay,followup in au.followups:
			async with message.channel.typing():
				await sleep(delay)
			await message.channel.send(followup)

		self.cooldowns['au'].update({user.id if await self.client.db.guild(message.guild.id).config.auto_responses.cooldown_per_user.read() else message.channel.id:int(time())})

		if responses == self.base_responses:
			user_data = await self.client.db.user(user.id).read()
			if raw_au not in user_data.get('data',{}).get('au').get(mode,[raw_au]) and not user_data.get('config',{}).get('general',{}).get('no_track',True):
				await self.client.db.user(user.id).data.au.append(raw_au,[mode])

		await self.client.log.listener(message,category=mode,trigger=raw_au)
		return True

	def rand_name(self,message:Message,splitter:str) -> str:
		options,weights = [message.guild.me.display_name if message.guild else self.client.user.name],[]
		if splitter in ["i'm"]:
			options += ['proud of you','not mad, just disappointed']
			weights += [0.005,0.01]
		weights.insert(0,1-sum(weights))
		return choices(options,weights)[0]

	async def listener_dad_bot(self,message:Message,user:MixedUser) -> None:
		response = ''
		input = sub(r"""<(@!|@|@&)\d{10,25}>|@everyone|@here|(https?:\/\/[^\s]+.)""",'[REDACTED]',sub(r'\*|\_|\~|\`|\|','',message.content))
		for p_splitter in ["i'm",'im','i am','i will be',"i've",'ive']:
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
		name = self.rand_name(message,splitter)

		if message.id not in self.timeouts: return False
		try: await message.channel.send(f'hi{response.split(".")[0]}, {splitter} {name}')
		except Forbidden: return False
		except HTTPException: await message.channel.send(f'hi{response.split(".")[0][:1936]} (character limit), {splitter} {name}')

		self.cooldowns['db'].update({user.id if await self.client.db.guild(message.guild.id).config.dad_bot.cooldown_per_user.read() else message.channel.id:int(time())})
		await self.client.log.listener(message,splitter=splitter,name=name)


def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(auto_response_listeners(client))