from utils.pycord_classes import SubCog
from discord.ext.commands import Cog


class ExtensionTalkingStickListeners(SubCog):
	@Cog.listener()
	async def on_ready(self) -> None:
		if not self.talking_stick_loop.is_running():
			self.talking_stick_loop.start()