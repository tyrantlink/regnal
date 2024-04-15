from utils.db.documents import Guild as GuildDocument
from utils.pycord_classes import SubCog
from discord import Guild,Member,Embed
from discord.ext.tasks import loop
from typing import AsyncIterator
from .models import QOTDPack
from client import Client


class ExtensionQOTDSubCog(SubCog):
	def __init__(self) -> None:
		self.client:Client
		self.recently_asked:set
		self.session_questions:dict[int,str]
		self.packs:dict[str,QOTDPack]
		self._guilds:tuple[int,list[tuple[Guild,GuildDocument]]]
		self._rescan:bool
		super().__init__()

	async def reload_packs(self) -> None: ...
	async def find_guilds(self) -> AsyncIterator[tuple[Guild,GuildDocument]]: ...
	async def log_ask_custom(self,author:Member,question:str) -> None: ...
	async def get_question(self,guild_doc:GuildDocument) -> tuple[GuildDocument,Embed]: ...
	async def ask_qotd(self,guild:Guild,guild_doc:GuildDocument) -> bool: ...

	@loop(seconds=1,count=1)
	async def qotd_loop(self) -> None: ...