from .subcog import ExtensionQOTDSubCog
from discord import Message,ChannelType
from discord.ext.commands import Cog


class ExtensionQOTDListeners(ExtensionQOTDSubCog):
	@Cog.listener()
	async def on_ready(self) -> None:
		await self.reload_packs()
		if not self.qotd_loop.is_running():
			self.qotd_loop.start()
	
	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if message.channel.id not in self.session_questions or message.author.bot:
			return
		metric = await self.client.db.qotd_metric(self.session_questions[message.channel.id])
		metric.responses += 1
		await metric.save_changes()