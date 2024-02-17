from .commands import ExtensionCryptographyCommands
from client import Client
from discord import Cog


class ExtensionCryptography(Cog,
	ExtensionCryptographyCommands
):
	def __init__(self,client:Client) -> None:
		self.client = client


def setup(client:Client) -> None:
	client.add_cog(ExtensionCryptography(client))
