from discord import Message, ChannelType, NotFound
from .subcog import ExtensionFunSubCog
from discord.ext.commands import Cog


class ExtensionFunListeners(ExtensionFunSubCog):
    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.reminder_loop.is_running():
            self.reminder_loop.start()
