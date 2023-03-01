from discord import Permissions,Embed,Object,Message
from discord.commands import Option as option,slash_command
from discord.ext.commands import Cog
from discord.errors import Forbidden
from client import Client


class nsfw_filter_listeners(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if not message.attachments or not message.embeds: return
		message.mentions



def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(nsfw_filter_listeners(client))