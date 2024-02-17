from .commands import ExtensionDevCommands
from .logic import ExtensionDevLogic
from discord.ext.commands import Cog
from client import Client

class ExtensionDev(Cog,
	ExtensionDevLogic,
	ExtensionDevCommands
):
	def __init__(self,client:Client) -> None:
		self.client = client


def setup(client:Client) -> None:
	client.add_cog(ExtensionDev(client))