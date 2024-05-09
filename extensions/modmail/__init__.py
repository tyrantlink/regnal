from utils.db.documents import Guild as GuildDocument
from discord.ext.commands import Cog
from .config import register_config
from discord import Guild
from client import Client
from .commands import ExtensionModMailCommands
from .views import ModMailPostedReportView
from .listeners import ExtensionModMailListeners


class ExtensionModMail(Cog,
	ExtensionModMailCommands,
	ExtensionModMailListeners
):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.client.add_view(ModMailPostedReportView(self.client,True))

def setup(client:Client) -> None:
	client.permissions.register_permission('modmail.close_thread')
	# client.permissions.register_permission('modmail.reopen_thread')
	client.add_cog(ExtensionModMail(client))
	register_config(client.config)