from discord.ext.commands import Cog
from discord import ApplicationContext
from main import client_cls
from statcord import Client

class statcord_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client
		self.key = self.client.env.statcord_key
		self.api = Client(self.client,self.key)
		self.api.start_loop()
	
	@Cog.listener()
	async def on_application_command(self,ctx:ApplicationContext) -> None:
		self.api.command_run(ctx)

def setup(client:client_cls) -> None: client.add_cog(statcord_cog(client))