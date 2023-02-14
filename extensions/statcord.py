from statcord import Client as Statcord
from discord import ApplicationContext
from discord.ext.commands import Cog
from client import Client


class statcord_listeners(Cog):
	def __init__(self,client:Client) -> None:
		self.api = Statcord(client,client.env.statcord_key)
		self.api.start_loop()

	@Cog.listener()
	async def on_application_command(self,ctx:ApplicationContext) -> None:
		self.api.command_run(ctx)

def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(statcord_listeners(client))