from discord import Embed,ApplicationContext
from discord.commands import slash_command
from discord.ext.commands import Cog
from main import client_cls

class help_cog(Cog):
	def __init__(self,client:client_cls):
		self.client = client

	@slash_command(
		name='help',
		description='get the /reg/nal help menu')
	async def slash_help(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(ephemeral=await self.client.hide(ctx),embed=Embed(title='/reg/nal help:',
		description='this is in development and also i\'m a dumbass that has too many other things that are probably more important but i\'ll get to it eventually when i\'m bored and feel like writing documentation.\nif you have a specific question, i might be able to help in the [development server](<https://discord.gg/4mteVXBDW7>).',color=await self.client.embed_color(ctx)))

def setup(client:client_cls):
	client.add_cog(help_cog(client))