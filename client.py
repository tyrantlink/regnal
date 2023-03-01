from discord import Interaction,ApplicationCommandInvokeError
from utils.classes import Env,ApplicationContext
from discord.ext.commands import AutoShardedBot
from utils.pluralkit import PluralKit
from utils.db import MongoDatabase
from utils.nsfw import nsfw
from utils.log import log

"""
i had to make this it's own file or it would initialize the client twice (once on startup, again on first extension load)
it's dumb and stupid and dumb and dumb and stupid but it fixes the bug and i don't care
"""

class Client(AutoShardedBot):
	def __init__(self,*args,**kwargs) -> None:
		super().__init__(*args,**kwargs)
		self.db:MongoDatabase
		self.flags:dict
		self.au:dict|None
		self.MODE:str
		self.env:Env
		self.log:log
		self.pk:PluralKit
		self.nsfw:nsfw|None
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

	def git_hash(self) -> None:
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