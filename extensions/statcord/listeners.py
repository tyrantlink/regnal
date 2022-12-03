from discord import ApplicationContext
from discord.ext.commands import Cog
from main import client_cls
from statcord import Client

class statcord_listeners(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.key = self.client.env.statcord_key
		self.api = Client(self.client,self.key)
		self.api.start_loop()
	
	@Cog.listener()
	async def on_application_command(self,ctx:ApplicationContext) -> None:
		self.api.command_run(ctx)