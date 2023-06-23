from discord import ApplicationContext as AppContext,Interaction,Embed,User,Member as DiscordMember,Message
from regex import search,fullmatch,escape,IGNORECASE
from discord.ui import View,Item,Modal,InputText
from utils.pluralkit import Member as PKMember
from utils.db.mongo_object import MongoObject
from pymongo.collection import Collection
from asyncio import wait_for,TimeoutError
from utils.sandbox import safe_exec
from functools import partial

class RestrictedMessage:
	class _channel:
		def __init__(self,id,name) -> None:
			self.id = id
			self.name = name

	class _guild:
		def __init__(self,id,name) -> None:
			self.id = id
			self.name = name

	class _user:
		def __init__(self,id,name,display_name) -> None:
			self.id = id
			self.name = name
			self.display_name = display_name

	def __init__(self,**kwargs):
		self.id = kwargs.get('message_id',None)
		self.channel = self._channel(
			kwargs.get('channel_id',None),
			kwargs.get('channel_name',None))
		self.guild = self._guild(
			kwargs.get('guild_id',None),
			kwargs.get('guild_name',None))
		self.author = self._user(
			kwargs.get('author_id',None),
			kwargs.get('author_name',None),
			kwargs.get('author_display_name',None))
		self.timestamp = kwargs.get('timestamp',None)
		self.content = kwargs.get('content',None)

class Env:
	def __init__(self,env_dict:dict) -> None:
		self.token:str = None
		self.dev_token:str = None
		self.beta_token:str = None
		self.tet_token:str = None
		self.mongo_pub:str = None
		self.mongo_prv:str = None
		self.config:dict = None
		self.activities:dict = None
		self.help:dict = None
		self.statcord_key:str = None
		self.saucenao_key:str = None
		for k,v in env_dict.items():
			setattr(self,k,v)

class MakeshiftClass:
	def __init__(self,**kwargs) -> None:
		"""attr=value will be set"""
		for k,v in kwargs.items():
			setattr(self,k,v)

class EmptyView(View):
	def __init__(self,*items:Item,timeout:float|None=180,disable_on_timeout:bool=False):
		tmp,self.__view_children_items__ = self.__view_children_items__,[]
		super().__init__(*items,timeout=timeout,disable_on_timeout=disable_on_timeout)
		self.__view_children_items__ = tmp
		for func in self.__view_children_items__:
			item: Item = func.__discord_ui_model_type__(**func.__discord_ui_model_kwargs__)
			item.callback = partial(func,self,item)
			item._view = self
			setattr(self,func.__name__,item)

	def add_items(self,*items:Item) -> None:
		for item in items:
			if item not in self.children: self.add_item(item)

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		embed = Embed(title='an error has occurred!',color=0xff6969)
		embed.add_field(name='error',value=str(error))
		await interaction.followup.send(embed=embed,ephemeral=True)

class CustomModal(Modal):
	def __init__(self,view:View|EmptyView,title:str,children:list[InputText]) -> None:
		self.view = view
		self.interaction = None
		super().__init__(*children,title=title)

	async def callback(self, interaction: Interaction):
		self.interaction = interaction
		self.stop()

class MixedUser:
	def __init__(self,type:str,raw:(User|DiscordMember)|PKMember,**kwargs) -> None:
		self.raw  = raw
		if type not in [
			'discord',
			'pluralkit']:
			raise ValueError(f'MixedUser type must be `discord` or `pluralkit` not {type}')
		self.type = type
		self.id:int|str
		self.name:str
		self.icon:str
		self.discriminator:str|None
		self.bot:bool

		for k,v in kwargs.items():
			setattr(self,k,v)

class AutoResponse:
	def __init__(self,_id:int,trigger:str,**kwargs) -> None:
		self._id          = _id
		self.trigger:str  = trigger
		self.method:str   = kwargs.get('method')
		self.response:str = kwargs.get('response',None)
		self.priority:int = kwargs.get('priority',0)
		self.custom:bool  = kwargs.get('custom',False)
		self.regex:bool   = kwargs.get('regex',False)
		self.nsfw:bool    = kwargs.get('nsfw',False)
		self.file:bool    = kwargs.get('file',False)
		self.cs:bool      = kwargs.get('case_sensitive',False)
		self.user:str     = kwargs.get('user',None)
		self.guild:str    = kwargs.get('guild',None)
		self.source:str   = kwargs.get('source',None)
		self.script:str	  = kwargs.get('script',None)
		self.alt_responses:list[tuple[float|int,str]] = [(w,r) for w,r in kwargs.get('alt_responses',[])]
		self.followups:list[tuple[float|int,str]] = [(w,r) for w,r in kwargs.get('followups',[])]
		self.overrides:dict[str,dict[str,str]] = kwargs.get('overrides',{})

		self.type = 'guild' if self.custom else 'unique' if self.guild else 'personal' if self.user else 'base'

	def __repr__(self) -> str:
		return f'<AutoResponse id={self._id} type={self.type} trigger="{self.trigger}" response="{self.response}">'

	def to_dict(self) -> dict:
		return {
			'_id':self._id,
			'trigger':self.trigger,
			'method':self.method,
			'response':self.response,
			'priority':self.priority,
			'custom':self.custom,
			'regex':self.regex,
			'nsfw':self.nsfw,
			'file':self.file,
			'case_sensitive':self.cs,
			'user':self.user,
			'guild':self.guild,
			'source':self.source,
			'script':self.script,
			'alt_responses':[[w,r] for w,r in self.alt_responses],
			'followups':[[w,r] for w,r in self.followups],
			'overrides':self.overrides}
	
	async def to_mongo(self,db:MongoObject,_id:int=None) -> None:
		data = self.to_dict()
		data.pop('_id')
		successful,new_id = await db.new(_id or self._id or '+1',data,update=True)
		if successful: self._id = new_id
		else: raise Exception(f'failed to write to mongo: {self.to_dict()}')

	async def run(self,message:Message,bypass_char_limit:bool=False) -> str:
		if self.script is None: return self.response
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
		try: output = await wait_for(safe_exec(self.script,{'message':restricted_message}),5)
		except TimeoutError: return
		response = output.get('response','')

		return response if (len(response) <= 512 or bypass_char_limit) else None

class AutoResponses:
	def __init__(self,db:Collection,filter:dict=None) -> None:
		self.db:Collection = db
		self.raw_au:list[dict] = []
		self.au:list[AutoResponse] = []
		self.custom_filter = filter is not None
		self.filter = {'_id':{'$ne':0}}
		if self.custom_filter: self.filter.update(filter)

	async def reload_au(self) -> None:
		self.raw_au = [d async for d in self.db.find(self.filter)]
		self.au = [AutoResponse(**i) for i in self.raw_au]

	def find(self,attrs:dict=None,limit:int=None) -> list[AutoResponse]:
		if attrs is None: return self.au
		out = []
		for au in self.au:
			if all(getattr(au,k) == v for k,v in attrs.items()):
				out.append(au)
				if limit is not None and len(out) >= limit: break
		return out

	def get(self,_id:int) -> AutoResponse|None:
		if res:= self.find({'_id':_id},1): return res[0]
		return None

	def match(self,message:Message,guild_id:int,attrs:dict=None) -> AutoResponse|None:
		position = None
		priority = None
		result   = None
		for au in sorted(filter(lambda d: all(getattr(d,k) == v for k,v in (attrs or {}).items()),self.au),key=lambda d: d.priority,reverse=True):
			trigger = au.overrides.get(str(guild_id),{}).get('trigger',au.trigger)
			match au.overrides.get(str(guild_id),{}).get('method',au.method):
				case 'exact': match = fullmatch((trigger if au.regex else escape(trigger))+r'(\.|\?|\!)*',message,0 if au.cs else IGNORECASE)
				case 'contains': match = search(rf'(^|\s){trigger if au.regex else escape(trigger)}(\.|\?|\!)*(\s|$)',message,0 if au.cs else IGNORECASE)
				case 'regex_raw': match = search(trigger,message,0 if au.cs else IGNORECASE)
				case _:
					match = None
					continue
			if match:
				if priority is None or au.priority >= priority:
					if position is None or match.span()[0] < position:
						position = match.span()[0]
						priority = au.priority
						result = au
					if position == 0: break
		return result

class ApplicationContext(AppContext):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.output:dict

class ArgParser:
	def __init__(self,message:str) -> None:
		self.delete:bool  = False
		self.alt:int|None = None
		self.au:int|None  = None
		self.force:bool   = False
		self.message:str  = None
		self.get_id:bool  = False
		self.parse(message)

	def parse(self,message:str) -> None:
		for loop in range(25):
			s = search(r'(.*)(?:^|\s)(--delete|--alt \d+|--au \d+|--force|--get-id)$',message,IGNORECASE)
			if s is None: break
			message = s.group(1)
			match s.group(2).split(' '):
				case ['--delete']: self.delete = True
				case ['--alt',a]: self.alt = int(a)
				case ['--au',a]: self.au = int(a)
				case ['--force']: self.force = True
				case ['--get-id']: self.get_id = True
				case _: continue
		self.message = message