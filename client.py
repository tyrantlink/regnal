from discord import ApplicationContext,Interaction,ApplicationCommandInvokeError,Embed,User,Member as DiscordMember
from utils.pluralkit import PluralKit,Member as PKMember
from discord.ui import View,Item,Modal,InputText
from discord.ext.commands import Bot
from functools import partial
from utils.data import db
from utils.log import log

"""
i had to make this it's own file or it would initialize the client twice (once on startup, again on first extension load)
it's dumb and stupid and dumb and dumb and stupid but it fixes the bug and i don't care
"""

class Client(Bot):
	def __init__(self,*args,**kwargs) -> None:
		super().__init__(*args,**kwargs)
		self.db:db
		self.flags:dict
		self.au:dict|None
		self.env:dict
		self.log:log
		self.pk:PluralKit
		self.loaded_extensions:list
		self._raw_loaded_extensions:list

	def generate_line_count(self):
		...

	async def _owner_init(self) -> None:
		...

	def _extloaded(self) -> None:
		...

	async def embed_color(self,ctx:ApplicationContext|Interaction) -> int:
		...

	async def hide(self,ctx:ApplicationContext|Interaction) -> bool:
		...
		
	async def on_connect(self) -> None:
		...
	
	async def on_ready(self) -> None:
		...

	async def on_application_command_completion(self,ctx:ApplicationContext) -> None:
		...

	async def on_unknown_application_command(self,interaction:Interaction) -> None:
		...

	async def on_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		...

	async def on_application_command_error(self,ctx:ApplicationContext|Interaction,error:ApplicationCommandInvokeError) -> None:
		...
	
	async def on_error(self,event:str,*args,**kwargs) -> None:
		...

class EmptyView(View):
	def __init__(self,*items:Item,timeout:float|None=180,disable_on_timeout:bool=False):
		self.client:Client
		self.embed:Embed

		tmp,self.__view_children_items__ = self.__view_children_items__,[]
		super().__init__(*items,timeout=timeout,disable_on_timeout=disable_on_timeout)
		self.__view_children_items__ = tmp
		for func in self.__view_children_items__:
			item: Item = func.__discord_ui_model_type__(**func.__discord_ui_model_kwargs__)
			item.callback = partial(func,self,item)
			item._view = self
			setattr(self,func.__name__,item)

	def add_items(self,*items:Item) -> None:
		for item in items: self.add_item(item)

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