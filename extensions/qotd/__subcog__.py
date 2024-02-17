from utils.db.documents import Guild as GuildDocument
from utils.pycord_classes import SubCog
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from typing import AsyncIterator
from discord import Guild,Member
from client import Client


class QOTDSubCog(SubCog):
	def __init__(self,client:Client) -> None:
		self.recently_asked:set
		self.packs:dict[str,list[str]]
		self._guilds:tuple[int,list[tuple[Guild,GuildDocument]]]
		self._rescan:bool
	@Cog.listener()
	async def on_ready(self) -> None: ...
	async def reload_packs(self) -> None: ...
	async def find_guilds(self) -> AsyncIterator[tuple[Guild,GuildDocument]]: ...
	async def log_ask_custom(self,author:Member,question:str) -> None: ...
	async def ask_qotd(self,guild:Guild,guild_doc:GuildDocument) -> bool: ...
	@loop(seconds=1)
	async def qotd_loop(self) -> None: ...