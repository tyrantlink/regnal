from .listeners import ExtensionMediaLinkFixerListeners
from .logic import ExtensionMediaLinkFixerLogic
from .config import register_config
from client import Client
from discord import Cog


class ExtensionAdmin(Cog,
	ExtensionMediaLinkFixerListeners,
	ExtensionMediaLinkFixerLogic
):
	def __init__(self,client:Client) -> None:
		self.client = client

def setup(client:Client) -> None:
	register_config(client.config)
	client.add_cog(ExtensionAdmin(client))