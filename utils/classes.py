from discord import Interaction,Embed,User,Message
from regex import search,fullmatch,escape,IGNORECASE
from discord.ui import View,Item,Modal,InputText
from pymongo.collection import Collection
from asyncio import wait_for,TimeoutError
from utils.sandbox import safe_exec
from functools import partial

from utils.db import AutoResponse
from utils.db import Guild

class OverriddenAutoResponse:
	class OverriddenData:
		class OverriddenFollowup:
			def __init__(self,delay:float,response:str) -> None:
				self.delay = delay
				self.response = response
		class OverriddenAlt:
			def __init__(self,chance:float,data:dict) -> None:
				self.chance = chance
				self.data = data #! this maybe has recursion potential, i'll deal with it later
		def __init__(self,au:AutoResponse.AutoResponseData,override:dict) -> None:
			self.priority = override.get('priority',au.priority)
			self.ignore_cooldown = override.get('ignore_cooldown',au.ignore_cooldown)
			self.custom = override.get('custom',au.custom)
			self.regex = override.get('regex',au.regex)
			self.nsfw = override.get('nsfw',au.nsfw)
			self.case_sensitive = override.get('case_sensitive',au.case_sensitive)
			self.users = override.get('users',au.users)
			self.guild = override.get('guild',au.guild)
			self.source = override.get('source',au.source)
			self.followups = [self.OverriddenFollowup(f.delay,f.response) for f in au.followups]
			self.alts = [self.OverriddenAlt(a.chance,a.data) for a in au.alts]

	def __init__(self,au:AutoResponse,override:dict) -> None:
		self._original = au
		self._override = override

		self.id = au.id
		self.method = override.get('method',au.method)
		self.trigger = override.get('trigger',au.trigger)
		self.response = override.get('response',au.response)
		self.type = override.get('type',au.type)
		self.data = self.OverriddenData(au.data,override.get('data',{}))

class AutoResponses:
	def __init__(self,filter:dict|None=None) -> None:
		self.filter = filter or {}
		self.au:list[AutoResponse] = []
		self.overrides:dict[int,dict[str,dict]] # {guild_id:{au_id:override_data}

	def __iter__(self) -> iter:
		return iter(self.au)

	def __len__(self) -> int:
		return len(self.au)

	async def reload_au(self,use_cache:bool=True) -> None:
		self.au = await AutoResponse.find(self.filter,ignore_cache=not use_cache).to_list()

	async def reload_overrides(self,guild_id:int|None,use_cache:bool=True) -> None:
		if guild_id is not None:
			guild = await Guild.find_one({'_id':guild_id},ignore_cache=not use_cache)
			if guild is None: raise Exception(f'guild {guild_id} not found')
			self.overrides[guild_id] = guild.data.auto_responses.overrides
			return None

		guilds = [g async for g in Guild.find_all(ignore_cache=not use_cache)]
		self.overrides = {g.id:g.data.auto_responses.overrides for g in guilds}

	def find(self,attrs:dict=None,limit:int=None) -> list[AutoResponse]:
		if attrs is None: return self.au
		out = []
		for au in self.au:
			if all(getattr(au,k) == v for k,v in attrs.items()):
				out.append(au)
				if limit is not None and len(out) >= limit: break
		return out

	def get(self,_id:int) -> AutoResponse|None:
		if res:=self.find({'_id':_id},1): return res[0]
		return None

	def match(self,message:Message,guild_id:int=None,attrs:dict=None) -> AutoResponse|None:
		position = None
		priority = None
		result   = None
		for au in sorted(filter(lambda d: all(getattr(d,k) == v for k,v in (attrs or {}).items()),self.au),key=lambda d: d.data.priority,reverse=True):
			if guild_id: au = OverriddenAutoResponse(au,self.overrides.get(guild_id,{}).get(au.id,{}))
			match au.method.name:
				case 'exact': match = fullmatch((au.trigger if au.data.regex else escape(au.trigger))+r'(\.|\?|\!)*',message,0 if au.data.case_sensitive else IGNORECASE)
				case 'contains': match = search(rf'(^|\s){au.trigger if au.data.regex else escape(au.trigger)}(\.|\?|\!)*(\s|$)',message,0 if au.data.case_sensitive else IGNORECASE)
				case 'regex': match = search(au.trigger,message,0 if au.data.case_sensitive else IGNORECASE)
				case _:
					match = None
					continue
			if match:
				if priority is None or au.data.priority >= priority:
					if position is None or match.span()[0] < position:
						position = match.span()[0]
						priority = au.data.priority
						result = au
					if position == 0: break
		return result