from aiohttp import ClientSession
from datetime import datetime
from time import perf_counter
from asyncio import sleep


BASEURL = 'https://api.pluralkit.me/v2'

class System:
	def __init__(self,raw:dict) -> None:
		self._raw:dict            = raw
		self.id:str               = raw.get('id')
		self.uuid:str             = raw.get('uuid')
		self.name:str             = raw.get('name')
		self.description:str|None = raw.get('description',None)
		self.tag:str|None         = raw.get('tag',None)
		self.pronouns:str|None    = raw.get('pronouns',None)
		self.avatar_url:str|None  = raw.get('avatar_url',None)
		self.banner:str|None      = raw.get('banner',None)
		self.color:str|None       = raw.get('color',None)
		self._created:str|None    = raw.get('datetime',None)

		self.created = None if self._created is None else datetime.fromisoformat(self._created[:-1] if self._created.endswith('Z') else self._created)

class ProxyTag:
	def __init__(self,raw:dict) -> None:
		self.prefix:str = raw.get('prefix',None)
		self.suffix:str = raw.get('suffix',None)

class Member:
	def __init__(self,raw:dict) -> None:
		self._raw:dict                        = raw
		self.id:str                           = raw.get('id')
		self.uuid:str                         = raw.get('uuid')
		self.name:str                         = raw.get('name')
		self.display_name:str                 = raw.get('display_name',self.name)
		self.color:str|None                   = raw.get('color',None)
		self.birthday:str|None                = raw.get('birthday',None)
		self.pronouns:str|None                = raw.get('pronouns',None)
		self.avatar_url:str|None              = raw.get('avatar_url',None)
		self.banner:str|None                  = raw.get('banner',None)
		self.description:str|None             = raw.get('description',None)
		self._created:str|None                = raw.get('datetime',None)
		self.proxy_tags:list[ProxyTag]        = [ProxyTag(i) for i in raw.get('proxy_tags',[])]
		self.keep_proxy:bool                  = raw.get('keep_proxy')
		self.autoproxy_enabled:bool|None      = raw.get('autoproxy_enabled',None)
		self.message_count:int|None           = raw.get('message_count',None)
		self._last_message_timestamp:str|None = raw.get('last_message_timestamp',None)

		if self.birthday: self.birthday           = self.birthday.replace('0004-','')
		self.created:datetime|None                = None if self._created is None else datetime.fromisoformat(self._created[:-1] if self._created.endswith('Z') else self._created)
		self.last_message_timestamp:datetime|None = None if self._last_message_timestamp is None else datetime.fromisoformat(self._last_message_timestamp.replace('Z','').ljust(26,'0'))

class Message:
	def __init__(self,raw:dict) -> None:
		self._raw:dict         = raw
		self.id:int            = int(raw.get('id'))
		self.original:int      = int(raw.get('original'))
		self.sender:int        = int(raw.get('sender'))
		self.channel:int       = int(raw.get('channel'))
		self.guild:int         = int(raw.get('guild'))
		self._system:dict|None = raw.get('system',None)
		self._member:dict|None = raw.get('member',None)

		self.system:System|None = None if self._system is None else System(self._system)
		self.member:Member|None = None if self._member is None else System(self._member)

class PluralKit:
	def __init__(self) -> None:
		self._recent_requests = []

	async def _handle_ratelimit(self) -> None:
		for ts in self._recent_requests.copy():
			if perf_counter()-ts > 1: self._recent_requests.remove(ts)
		if len(self._recent_requests) >= 2:
			await sleep(perf_counter()-self._recent_requests[0])
			await self._handle_ratelimit()

	async def request(self,endpoint:str):
		await self._handle_ratelimit()
		async with ClientSession() as session:
			async with session.get(f'{BASEURL}{endpoint}') as res:
				self._recent_requests.append(perf_counter())
				return (res.status == 200,await res.json())

	async def get_system(self,discord_id:str|int) -> System|None:
		req = await self.request(f'/systems/{discord_id}')
		if req[0]: return System(req[1])
		else: return None

	async def get_members(self,discord_id:str|int) -> list[Member]:
		req = await self.request(f'/systems/{discord_id}/members')
		if req[0]: return [Member(m) for m in req[1]]
		else: return None

	async def get_member(self,uuid:str) -> Member|None:
		req = await self.request(f'/members/{uuid}')
		if req[0]: return Member(req[1])
		else: return None

	async def get_message(self,message_id:str,delay:float=0.2) -> Message|None:
		await sleep(delay)
		req = await self.request(f'/messages/{message_id}')
		if req[0]: return Message(req[1])
		else: return None