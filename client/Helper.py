from discord import ApplicationContext,Interaction
from utils.db import MongoDatabase
from utils.db.documents.ext.enums import TWBFMode


class ClientHelpers:
	def __init__(self,db:MongoDatabase) -> None:
		self.db = db

	async def embed_color(self,ctx:ApplicationContext|Interaction) -> int:
		if ctx.guild: return int((await self.db.guild(ctx.guild_id)).config.general.embed_color,16)
		else: return int('69ff69',16)

	async def ephemeral(self,ctx:ApplicationContext|Interaction) -> bool:
		if ctx.guild:
			guild = await self.db.guild(ctx.guild_id)
			match guild.config.general.hide_commands:
				case TWBFMode.true: return True
				case TWBFMode.whitelist if ctx.channel_id in guild.data.hide_commands.whitelist: return True
				case TWBFMode.blacklist if ctx.channel_id not in guild.data.hide_commands.blacklist: return True
				case TWBFMode.false: pass
		return (await self.db.user(ctx.user.id)).config.general.hide_commands