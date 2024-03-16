from utils.db.documents import Guild as GuildDocument
from utils.pycord_classes import SubCog
from discord.ext.tasks import loop
from typing import AsyncIterator
from discord import Guild
from client import Client


class ExtensionTalkingStickSubCog(SubCog):
	def __init__(self) -> None:
		self.client:Client
		self.recently_rolled:set
		self._guilds:tuple[int,list[tuple[Guild,GuildDocument]]]
		self._rescan:bool
		super().__init__()

	async def find_guilds(self) -> AsyncIterator[tuple[Guild,GuildDocument]]: ...
	async def roll_complete(self,guild_id:int) -> None: ...
	async def roll_talking_stick(self,guild:Guild,guild_doc:GuildDocument) -> bool: ...

	@loop(seconds=1,count=1)
	async def talking_stick_loop(self) -> None: ...