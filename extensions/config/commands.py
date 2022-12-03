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
		allowed_config = ['user']
		if ctx.guild:
			if ctx.author.guild_permissions.manage_guild:
				allowed_config.append('guild')
				if ctx.author.guild_permissions.view_audit_log: allowed_config.append('logging')
		if await dev_only(ctx): allowed_config.append('/reg/nal')
		embed_color = await self.client.embed_color(ctx)
		embed = Embed(title='config options',description='please select a config category',color=embed_color)
		await ctx.response.send_message(embed=embed,view=config_view(
			client=self.client,
			allowed_config=allowed_config,
			embed=embed,
			embed_color=embed_color),
			ephemeral=True)
