from .subcog import ExtensionQOTDSubCog
from discord.ext.commands import Cog


class ExtensionQOTDListeners(ExtensionQOTDSubCog):
	@Cog.listener()
	async def on_ready(self) -> None:
		await self.reload_packs()
		if not self.qotd_loop.is_running():
			self.qotd_loop.start()