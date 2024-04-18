from client import Client
from discord.ext.commands import Cog
from .commands import CustomBotMariCommands


class CustomBotMari(Cog,
	CustomBotMariCommands
):
	def __init__(self,client:Client):
		self.client = client


def setup(client:Client):
	client.add_cog(CustomBotMari(client))