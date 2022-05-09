from discord.ext.commands import Cog
from main import client_cls

class feature_test(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

def setup(client:client_cls) -> None: client.add_cog(feature_test(client))