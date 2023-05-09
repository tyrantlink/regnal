from discord import ApplicationContext as AppContext,Interaction,Embed,User,Member as DiscordMember
from regex import search,fullmatch,escape,IGNORECASE
from discord.ui import View,Item,Modal,InputText
from utils.pluralkit import Member as PKMember
from utils.db.mongo_object import MongoObject
from pymongo.collection import Collection
from functools import partial

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
		self.custom:bool  = kwargs.get('custom',False)
		self.regex:bool   = kwargs.get('regex',False)
		self.nsfw:bool    = kwargs.get('nsfw',False)
		self.file:bool    = kwargs.get('file',False)
		self.cs:bool      = kwargs.get('cs',False)
		self.user:str     = kwargs.get('user',None)
		self.guild:str    = kwargs.get('guild',None)
		self.source:str   = kwargs.get('source',None)
		self.alt_responses:list[tuple[float|int,str]] = [(w,r) for w,r in kwargs.get('alt_responses',[])]
		self.followups:list[tuple[float|int,str]] = [(w,r) for w,r in kwargs.get('followups',[])]

	def to_dict(self) -> dict:
		return {
			'_id':self._id,
			'trigger':self.trigger,
			'method':self.method,
			'response':self.response,
			'custom':self.custom,
			'regex':self.regex,
			'nsfw':self.nsfw,
			'file':self.file,
			'case_sensitive':self.cs,
			'user':self.user,
			'guild':self.guild,
			'source':self.source,
			'alt_responses':[[w,r] for w,r in self.alt_responses],
			'followups':[[w,r] for w,r in self.followups]}
	
	async def to_mongo(self,db:MongoObject,_id:int=None) -> None:
		data = self.to_dict()
		data.pop('_id')
		await db.new(_id or self._id or '+1',data)

class AutoResponses:
	def __init__(self,db:Collection) -> None:
		self.db:Collection = db
		self.raw_au:list[dict] = []
		self.au:list[AutoResponse] = []

	async def reload_au(self) -> None:
		self.raw_au = [d async for d in self.db.find({'_id':{'$ne':0}})]
		self.au = [AutoResponse(**i) for i in self.raw_au]

	def find(self,attrs:dict,limit:int=None) -> list[AutoResponse]|None:
		out = []
		for au in self.au:
			if all(getattr(au,k) == v for k,v in attrs.items()):
				out.append(au)
				if limit is not None and len(out) >= limit: break
		return out

	def get(self,_id:int) -> AutoResponse|None:
		return self.find({'_id':_id},1)[0]

	def match(self,message:str,attrs:dict=None) -> AutoResponse|None:
		out = (None,None)
		for au in list(filter(lambda d: all(d[k] == v for k,v in (attrs or {}).items()),self.au)):
			match au.method:
				case 'exact': match = fullmatch((au.trigger if au.regex else escape(au.trigger))+r'(\.|\?|\!)*',message,0 if au.cs else IGNORECASE)
				case 'contains': match = search(rf'(^|\s){au.trigger if au.regex else escape(au.trigger)}(\.|\?|\!)*(\s|$)',message,0 if au.cs else IGNORECASE)
				case _:
					match = None
					continue
			if match:
				if out[0] is None or match.span()[0] < out[0]: out = (match.span()[0],au)
				if out[0] == 0: break
		return out[1]

class ApplicationContext(AppContext):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.output:dict