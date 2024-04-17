from discord import Message,ChannelType,NotFound
from .subcog import ExtensionQOTDSubCog
from discord.ext.commands import Cog


class ExtensionQOTDListeners(ExtensionQOTDSubCog):
	@Cog.listener()
	async def on_ready(self) -> None:
		await self.reload_packs()
		if not self.qotd_loop.is_running():
			self.qotd_loop.start()

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if (
			not message.channel.type == ChannelType.public_thread or
			message.channel.owner_id != self.client.user.id or
			message.author.bot):
			return

		try:
			starting_message = (
				message.channel.starting_message or
				await message.channel.fetch_message(message.channel.id))
		except NotFound:
			return

		if starting_message.author.id != self.client.user.id or not starting_message.embeds:
			return

		metric = await self.client.db.qotd_metric(starting_message.embeds[0].footer.text)
		metric.responses += 1
		await metric.save_changes()