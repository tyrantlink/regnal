from .listeners import BotExtensionTetListeners
from .commands import BotExtensionTetCommands
from discord.ext.commands import Cog
from client import Client

#? most of this extension is hardcoded garbage because i don't want to go through the effort of making it a real feature

class BotExtensionTet(Cog,
	BotExtensionTetListeners,
	BotExtensionTetCommands
):
	def __init__(self,client:Client):
		self.client = client

def setup(client:Client):
	client.add_cog(BotExtensionTet(client))