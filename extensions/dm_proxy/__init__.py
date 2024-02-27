from .listeners import ExtensionDMProxyListeners
from discord.ext.commands import Cog
from client import Client


class ExtensionDMProxy(Cog,
	ExtensionDMProxyListeners
):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.bot_info_cache = {}


def setup(client:Client) -> None:
	client.add_cog(ExtensionDMProxy(client))