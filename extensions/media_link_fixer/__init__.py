from .listeners import ExtensionMediaLinkFixerListeners
from .logic import ExtensionMediaLinkFixerLogic
from .config import register_config
from client import Client
from discord import Cog


class ExtensionMediaLinkFixer(Cog,
	ExtensionMediaLinkFixerListeners,
	ExtensionMediaLinkFixerLogic
):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.embed_cache = {}

def setup(client:Client) -> None:
	register_config(client.config)
	client.add_cog(ExtensionMediaLinkFixer(client))