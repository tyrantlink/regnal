from utils.db.documents.ext.enums import AutoResponseMethod
from regex import search,fullmatch,escape,IGNORECASE
from discord.errors import HTTPException,Forbidden
from asyncio import sleep,create_task
from utils.db import AutoResponse
from discord import Message
from typing import TypeVar
from random import random
from client import Client

A = TypeVar('A')

class ArgParser:
	def __init__(self,message:str) -> None:
		self.delete:bool  = False
		self.seed:int|None = None
		self.au:int|None  = None
		self.force:bool   = False
		self.message:str  = None
		self.parse(message)

	def __bool__(self) -> bool:
		return (self.delete is True or
						self.seed is not None or
						self.au is not None or
						self.force is True)

	def parse(self,message:str) -> None:
		for _ in range(5):
			s = search(r'(.*)(?:^|\s)((?:--delete|-d)|(?:--force-index|-i) \d+|(?:--au|-a) (?:b|c|u|m|p|g)\d+|(?:--force|-f))$',message,IGNORECASE)
			if s is None: break
			message = s.group(1)
			match s.group(2).split(' '):
				case ['--delete']|['-d']: self.delete = True
				case ['--seed',a]|['-s',a]: self.seed = int(a)
				case ['--au',a]|['-a',a]: self.au = a
				case ['--force']|['-f']: self.force = True
				case _: continue
		self.message = message

class AutoResponseCarrier:
	def __init__(self,au:list[AutoResponse]) -> None:
		self.all = au
		self.base = list(filter(lambda d: d.id.startswith('b'),au))
		self._custom = list(filter(lambda d: d.id.startswith('c'),au))
		self._unique = list(filter(lambda d: d.id.startswith('u'),au))
		self._mention = list(filter(lambda d: d.id.startswith('m'),au))
		self._personal = list(filter(lambda d: d.id.startswith('p'),au))
		self._scripted = list(filter(lambda d: d.id.startswith('s'),au))

	def custom(self,guild_id:int) -> list[AutoResponse]:
		return list(filter(lambda au: au.data.guild == guild_id,self._custom))

	def unique(self,guild_id:int) -> list[AutoResponse]:
		return list(filter(lambda au: au.data.guild == guild_id,self._unique))

	def mention(self,user_id:int=None,user_ids:list[int]=None) -> list[AutoResponse]:
		if user_id and user_ids: raise ValueError('cannot specify both user_id and user_ids')
		if user_id: return list(filter(lambda au: au.trigger == str(user_id),self._mention))
		if user_ids: return list(filter(lambda au: au.trigger in [str(a) for a in user_ids],self._mention))
		return self._mention

	def personal(self,user_id:int) -> list[AutoResponse]:
		return list(filter(lambda au: au.data.user == user_id,self._personal))

	def scripted(self,guild_imported:set[str]) -> list[AutoResponse]:
		return list(filter(lambda au: au.id in guild_imported,self._scripted))

class AutoResponses:
	def __init__(self,client:Client|None=None) -> None:
		self.client = client
		self.au:AutoResponseCarrier = AutoResponseCarrier([])

	def __iter__(self) -> iter:
		return iter(self.au)

	def __len__(self) -> int:
		return len(self.au)

	async def reload_au(self,use_cache:bool=True) -> None:
		self.au = AutoResponseCarrier(await AutoResponse.find(ignore_cache=not use_cache).to_list())

	def find(self,attrs:dict=None,limit:int=None) -> list[AutoResponse]:
		if attrs is None: return self.au
		out = []
		for au in self.au.all:
			if all(getattr(au,k) == v for k,v in attrs.items()):
				out.append(au)
				if limit is not None and len(out) >= limit: break
		return out

	def get(self,_id:str) -> AutoResponse|None:
		if res:=self.find({'id':_id},1): return res[0]
		return None

	def match(self,message:str,overrides:dict,pool:list[AutoResponse]|None=None) -> list[AutoResponse]:
		if pool is None: pool = self.au.all
		found = []
		for au in pool:
			au = au.with_overrides(overrides[au.id]) if au.id in overrides else au
			match au.method:
				case AutoResponseMethod.exact: match = fullmatch((au.trigger if au.data.regex else escape(au.trigger))+r'(\.|\?|\!)*',message,0 if au.data.case_sensitive else IGNORECASE)
				case AutoResponseMethod.contains: match = search(rf'(^|\s){au.trigger if au.data.regex else escape(au.trigger)}(\.|\?|\!)*(\s|$)',message,0 if au.data.case_sensitive else IGNORECASE)
				case AutoResponseMethod.regex: match = search(au.trigger,message,0 if au.data.case_sensitive else IGNORECASE)
				case AutoResponseMethod.mention: match = search(rf'<@!?{au.trigger}>(\s|$)',message,0 if au.data.case_sensitive else IGNORECASE)
				case AutoResponseMethod.disabled: continue
				case _: raise ValueError(f'invalid auto response method: {au.method}')
			if match is not None:
				found.append(au)
		return found

	async def notify_reaction(self,message:Message) -> None:
		try:
			await message.add_reaction('❌')
			await sleep(1)
			await message.remove_reaction('❌',self.client.user)
		except (HTTPException,Forbidden): pass

	def random_choice(self,pool:list[tuple[A,int|None]]) -> A:
		choices,weights = zip(*pool)
		rand = random()*sum(weights)
		cum = 0 # please, it stands for cumulative
		for choice,weight in zip(choices,weights):
			cum += weight
			if rand <= cum: return choice
		raise ValueError(f'random choice failed with {rand=}, {cum=}, {sum(weights)=}')

	async def get_response(self,message:Message,args:ArgParser,overrides:dict[str,dict],cross_guild:bool=False) -> AutoResponse|None:
		if self.client is None: raise ValueError('AutoResponses object must have client set to get response')
		if message.guild is None: raise ValueError('message must be from a guild!')
		# check if --au can be used, return if so
		_user = await self.client.db.user(message.author.id)
		user_found = _user.data.auto_responses.found if _user else []
		if args.au is not None and not args.force:
			if (
				(response:=self.get(args.au)) and 
				(response.id in user_found and
				(response.data.guild in [message.guild.id,None] or cross_guild) or cross_guild)):
					return response
			create_task(self.notify_reaction(message))
		imported_scripts = set((await self.client.db.guild(message.guild.id)).data.auto_responses.imported_scripts)
		# gather matches
		matches = [
			*self.match(args.message,overrides,self.au.personal(message.author.id)), # personal responses
			*self.match(args.message,overrides,self.au.mention(
				user_ids=[a.id for a in message.mentions if f'<@{a.id}>' in args.message])), # mention responses
			*self.match(args.message,overrides,self.au.custom(message.guild.id)), # custom responses
			*self.match(args.message,overrides,self.au.unique(message.guild.id)), # unique responses
			*self.match(args.message,overrides,self.au.scripted(imported_scripts)), # scripted responses
			*self.match(args.message,overrides,self.au.base)] # base responses
		if not matches: return None
		if args.seed is not None:
			if not (args.seed > (len(matches)+1)):
				alt = matches[args.seed]
				if args.force or alt.id in user_found:
					return alt
			create_task(self.notify_reaction(message))
		# choose a match
		response = self.random_choice([(a,a.data.weight) for a in matches])
		# insert regex groups
		if response.data.regex and (match:=search(response.trigger,args.message,IGNORECASE)):
			groups = {f'g{i}':'' for i in range(1,11)}
			groups.update({f'g{k}':v for k,v in enumerate(match.groups()[:10],1) if v is not None})
			try: response = response.with_overrides({'response':response.response.format(**groups)})
			except KeyError: return None

		return response

	async def execute_au(self,id:str,message:Message) -> tuple[str,AutoResponse.AutoResponseData.AutoResponseFollowup]:
		raise NotImplementedError('scripted auto responses are not supported yet!') #! implement this with lua or something dumbass
		return response,followups