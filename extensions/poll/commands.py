from .views import poll_published_view,poll_view
from discord import Embed,ApplicationContext
from discord.commands import slash_command
from discord.ext.commands import Cog
from client import Client


class poll_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	@Cog.listener()
	async def on_ready(self) -> None:
		self.client.add_view(poll_published_view(client=self.client))

	@slash_command(name='poll',
		description='create a poll',
		guild_only=True)
	async def slash_poll(self,ctx:ApplicationContext) -> None:
		embed = Embed(title='set a poll title!',description='and the description too!\nif you want, i guess. a description isn\'t required.',color=await self.client.embed_color(ctx))
		await ctx.response.send_message(embed=embed,
		view=poll_view(
			client=self.client,
			embed=embed),
			ephemeral=True)
