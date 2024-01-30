from utils.db.documents.ext.enums import AutoResponseMethod,AutoResponseType
from .script_handler import RestrictedMessage,safe_exec
from regex import search,fullmatch,escape,IGNORECASE
from discord.errors import HTTPException,Forbidden
from asyncio import sleep,create_task,wait_for
from utils.db import AutoResponse
from discord import Message
from random import random
from client import Client
from typing import Any


class ArgParser:
	def __init__(self,message:str) -> None:
		self.delete:bool  = False
		self.alt:int|None = None
		self.au:int|None  = None
		self.force:bool   = False
		self.message:str  = None
		self.get_id:bool  = False
		self.parse(message)

	def __bool__(self) -> bool:
		return (self.delete is True or
						self.alt is not None or
						self.au is not None or
						self.force is True or
						self.get_id is True)

	def parse(self,message:str) -> None:
		for loop in range(25):
			s = search(r'(.*)(?:^|\s)((?:--delete|-d)|(?:--alt|-l) \d+|(?:--au|-a) (?:b|c|u|m|p|g)\d+|(?:--force|-f)|(?:--get-id|-i))$',message,IGNORECASE)
			if s is None: break
			message = s.group(1)
			match s.group(2).split(' '):
				case ['--delete']|['-d']: self.delete = True
				case ['--alt',a]|['-l',a]: self.alt = int(a)
				case ['--au',a]|['-a',a]: self.au = a
				case ['--force']|['-f']: self.force = True
				case ['--get-id']|['-i']: self.get_id = True
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

	def custom(self,guild_id:int) -> list[AutoResponse]:
		return list(filter(lambda d: d.data.guild == guild_id,self._custom))

	def unique(self,guild_id:int) -> list[AutoResponse]:
		return list(filter(lambda d: d.data.guild == guild_id,self._unique))

	def mention(self,user_id:int=None,user_ids:list[int]=None) -> list[AutoResponse]:
		if user_id and user_ids: raise ValueError('cannot specify both user_id and user_ids')
		if user_id: return list(filter(lambda d: d.trigger == str(user_id),self._mention))
		if user_ids: return list(filter(lambda d: d.trigger in [str(a) for a in user_ids],self._mention))
		return []

	def personal(self,user_id:int) -> list[AutoResponse]:
		return list(filter(lambda d: user_id == d.data.user,self._personal))

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

	def match(self,message:str,pool:list[AutoResponse]|None=None) -> list[AutoResponse]:
		if pool is None: pool = self.au.all
		found = []
		for au in pool:
			match au.method:
				case AutoResponseMethod.exact: match = fullmatch((au.trigger if au.data.regex else escape(au.trigger))+r'(\.|\?|\!)*',message,0 if au.data.case_sensitive else IGNORECASE)
				case AutoResponseMethod.contains: match = search(rf'(^|\s){au.trigger if au.data.regex else escape(au.trigger)}(\.|\?|\!)*(\s|$)',message,0 if au.data.case_sensitive else IGNORECASE)
				case AutoResponseMethod.regex: match = search(au.trigger,message,0 if au.data.case_sensitive else IGNORECASE)
				case AutoResponseMethod.mention: match = search(rf'<@!?{au.trigger}>(\s|$)',message,0 if au.data.case_sensitive else IGNORECASE)
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

	def random_choice(self,pool:list[tuple[Any,int|None]]) -> Any:
		choices,weights = zip(*pool)
		if None in weights: # auto balance None values
			balanced_weight = round(10000-sum([a for a in weights if a is not None]))/len([a for a in weights if a is None])
			weights = [a or balanced_weight for a in weights]

		if sum(weights) != 10000: raise ValueError('sum of weights must equal 10000')
		rand = random()*10000
		cum = 0 # please, it stands for cumulative
		for choice,weight in zip(choices,weights):
			cum += weight
			if rand <= cum: return choice

	async def get_response(self,message:Message,args:ArgParser,cross_guild:bool=False) -> AutoResponse|None:
		if self.client is None: raise ValueError('AutoResponses object must have client set to get response')
		if message.guild is None: raise ValueError('message must be from a guild!')
		# check if --au can be used, return if so
		_user = await self.client.db.user(message.author.id)
		user_found = _user.data.auto_responses.found if _user else []
		if args.au is not None:
			if (
				(response:=self.get(args.au)) and 
				(response.id in user_found and
				(response.data.guild in [message.guild.id,None] or cross_guild) or cross_guild)):
					return response
			create_task(self.notify_reaction(message))
		# gather matches
		matches = [
			*self.match(args.message,self.au.personal(message.author.id)), # personal responses
			*self.au.mention(user_ids=[a.id for a in message.mentions if f'<@{a.id}>' in args.message]), # mention responses
			*self.match(args.message,self.au.custom(message.guild.id)), # custom responses
			*self.match(args.message,self.au.unique(message.guild.id)), # unique responses
			*self.match(args.message,self.au.base)] # base responses
		if not matches: return None
		if args.alt is not None:
			if not (args.alt > (len(matches)+1)):
				alt = matches[args.alt]
				if args.force or alt.id in user_found:
					return alt
			create_task(self.notify_reaction(message))
		# choose a match and return it
		response:AutoResponse = self.random_choice([(a,a.data.weight) for a in matches])
		if response.data.chance is not None and self.random_choice([(True,response.data.chance),(False,None)]):
			return None
		return response

	async def execute_au(self,id:str,message:Message) -> tuple[str,AutoResponse.AutoResponseData.AutoResponseFollowup]:
		au = self.get(id)
		if au is None: raise ValueError(f'no auto response found with id {id}')
		if au.type != AutoResponseType.script: raise ValueError(f'auto response {id} is not a script')
		restricted_message = RestrictedMessage(
			message_id=message.id,
			channel_id=message.channel.id,
			channel_name=message.channel.name,
			guild_id=message.guild.id,
			guild_name=message.guild.name,
			author_id=message.author.id,
			author_name=message.author.name,
			author_display_name=message.author.display_name,
			timestamp=message.created_at.timestamp(),
			content=message.content)
		try: output = await wait_for(safe_exec(au.response,{'message':restricted_message}),5)
		except TimeoutError: return
		response = output.get('response','')
		followups = [AutoResponse.AutoResponseData.AutoResponseFollowup(delay=d,response=r) for d,r in output.get('followups',[])]
		if len(followups) > 10: return
		if any([(len(response) > 512) or (delay > 60) for delay,response in [(0,response),*[(f.delay,f.response) for f in followups]]]):
			raise ValueError('response cannot exceed 512 characters')
		return response,followups