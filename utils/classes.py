from discord import ApplicationContext as AppContext,Interaction,Embed,User,Member as DiscordMember
from discord.ui import View,Item,Modal,InputText
from utils.pluralkit import Member as PKMember
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
	def __init__(self,trigger:str,**kwargs) -> None:
		self.trigger:str  = trigger
		self.method:str   = kwargs.get('method')
		self.regex:bool   = kwargs.get('regex',False)
		self.nsfw:bool    = kwargs.get('nsfw',False)
		self.file:bool    = kwargs.get('file',False)
		self.user:str     = kwargs.get('user',None)
		self.guild:str    = kwargs.get('guild',None)
		self.response:str = kwargs.get('response',None)
		self.alt_responses:list[str] = kwargs.get('alt_responses',[])
		self.case_sensitive:bool = kwargs.get('case_sensitive',False)
		self.alt_weights:list[float] = kwargs.get('multi_weights',None)
		self.followups:list[tuple[float,str]] = kwargs.get('followups',[])

	def to_dict(self,guild_only:bool=True,include_trigger:bool=False) -> dict:
		res = {'trigger':self.trigger} if include_trigger else {}
		res.update({
			'method':self.method,
			'response':self.response,
			'regex':self.regex,
			'nsfw':self.nsfw,
			'user':self.user,
			'case_sensitive':self.case_sensitive,})
		if guild_only: return res
		res.update({
			'file':self.file,
			'guild':self.guild,
			'alt_responses':self.alt_responses,
			'alt_weights':self.alt_weights,
			'followups':self.followups})
		return res

class ApplicationContext(AppContext):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.output:dict