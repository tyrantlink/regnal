from discord.commands import slash_command
from discord import ApplicationContext
from .views.guild import guild_config
from discord.ext.commands import Cog
from .views.user import user_config
from .views.home import home_view
from .views.dev import dev_config
from client import Client


class config_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	@slash_command(
		name='config',
		description='set config')
	async def slash_config(self,ctx:ApplicationContext) -> None:
		embed_color = await self.client.embed_color(ctx)
		view = home_view(
			client=self.client,
			user=ctx.author,
			guild=ctx.guild,
			dev_bypass=await self.client.db.inf.read('/reg/nal',['config','bypass_permissions']),
			embed_color=embed_color)
		if len(view.options) == 1:
			match view.options[0].label:
				case 'user': view = user_config(None,self.client,ctx.author,embed_color)
				case 'guild': view = guild_config(None,self.client,ctx.author,ctx.guild,embed_color)
				case 'user': view = dev_config(None,self.client,embed_color)
				case _: raise ValueError('improper option selected, this probably shouldn\'t be possible')
			await view.start()
		await ctx.response.send_message(embed=view.embed,view=view,ephemeral=True)
