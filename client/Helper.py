from discord import ApplicationContext,Interaction,Embed
from utils.db.documents.ext.enums import TWBFMode
from utils.db import MongoDatabase


class ClientHelpers:
	def __init__(self,db:MongoDatabase) -> None:
		self.db = db

	async def embed_color(self,guild_id:int=None) -> int:
		if guild_id is None: return int('69ff69',16)
		else: return int((await self.db.guild(guild_id)).config.general.embed_color,16)

	async def ephemeral(self,ctx:ApplicationContext|Interaction) -> bool:
		if ctx.guild:
			guild = await self.db.guild(ctx.guild_id)
			match guild.config.general.hide_commands:
				case TWBFMode.true: return True
				case TWBFMode.whitelist if ctx.channel_id in guild.data.hide_commands.whitelist: return True
				case TWBFMode.blacklist if ctx.channel_id not in guild.data.hide_commands.blacklist: return True
				case TWBFMode.false: pass
		return (await self.db.user(ctx.user.id)).config.general.hide_commands

	async def error_response(self,ctx:ApplicationContext|Interaction,error:str,description:str=None) -> None:
		await ctx.send(embed=Embed(
				title='PERMISSION ERROR',
				description='i am missing either `Manage Messages` or `Read Message History`\nbe sure to check both my integration role and channel overrides',color=0xff6969),
			ephemeral=await self.client.hide(ctx))