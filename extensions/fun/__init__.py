from .commands import ExtensionFunCommands
from discord.ext.commands import Cog
from client import Client


class ExtensionFun(Cog,
	ExtensionFunCommands
):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.bees_running = set()


def setup(client:Client) -> None:
	client.add_cog(ExtensionFun(client))