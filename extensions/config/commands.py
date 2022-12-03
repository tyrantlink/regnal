from discord import Embed,ApplicationContext
from discord.commands import slash_command
from discord.ext.commands import Cog
from utils.tyrantlib import dev_only
from .views import config_view
from main import client_cls


class config_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	@slash_command(
		name='config',
		description='set config')
	async def slash_config(self,ctx:ApplicationContext) -> None:
		embed = Embed(title='config',color=await self.client.embed_color(ctx))
		view = config_view(
			client=self.client,
			embed=embed,
			user=ctx.author,
			current_config={
				'user':await self.client.db.users.read(ctx.author.id,['config']),
				'guild':await self.client.db.guilds.read(ctx.guild.id,['config']),
				'dev':await self.client.db.inf.read('/reg/nal',['config'])})
		await ctx.response.send_message(embed=embed,view=view,
			ephemeral=True)
