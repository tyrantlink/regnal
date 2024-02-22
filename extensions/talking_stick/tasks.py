from utils.pycord_classes import SubCog
from discord.ext.tasks import loop
from datetime import datetime
from pytz import timezone


class ExtensionTalkingStickTasks(SubCog):
	@loop(seconds=1)
	async def talking_stick_loop(self) -> None:
		if not self.client.is_ready(): return
		async for guild,guild_doc in self.find_guilds():
			# ensure it's the right time
			if datetime.now(timezone(
				guild_doc.config.general.timezone)).strftime('%H:%M') != guild_doc.config.talking_stick.time: continue

			self.client.log.debug(f'rolling talking stick',guild.id)
			await self.roll_talking_stick(guild,guild_doc)