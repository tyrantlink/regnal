from .subcog import ExtensionQOTDSubCog
from discord.ext.tasks import loop
from datetime import datetime
from pytz import timezone

class ExtensionQOTDTasks(ExtensionQOTDSubCog):
	@loop(seconds=1)
	async def qotd_loop(self) -> None:
		if not self.client.is_ready(): return
		async for guild,guild_doc in self.find_guilds():
			# ensure it's the right time
			if datetime.now(timezone(
				guild_doc.config.general.timezone)).strftime('%H:%M') != guild_doc.config.qotd.time: continue
			await self.ask_qotd(guild,guild_doc)
			if self._rescan: break