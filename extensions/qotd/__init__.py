from utils.db.documents import Guild as GuildDocument
from .listeners import ExtensionQOTDListeners
from .logic import ExtensionQOTDLogic
from .tasks import ExtensionQOTDTasks
from .commands import ExtensionQOTDCommands
from discord.ext.commands import Cog
from .config import register_config
from discord import Guild
from client import Client
from .views import QOTDAskLog


class ExtensionQOTD(Cog,
	ExtensionQOTDLogic,
	ExtensionQOTDListeners,
	ExtensionQOTDTasks,
	ExtensionQOTDCommands
):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.recently_asked = set()
		self.packs:dict[str,list[str]] = {}
		self._guilds:tuple[int,list[tuple[Guild,GuildDocument]]] = (0,set())
		self._rescan = False
		self.client.add_view(QOTDAskLog(self.client))


def setup(client:Client) -> None:
	client.permissions.register_permission('qotd.remove_custom')
	client.add_cog(ExtensionQOTD(client))
	register_config(client.config)