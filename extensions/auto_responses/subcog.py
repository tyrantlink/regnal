from utils.pycord_classes import SubCog
from .classes import ArgParser
from discord import Message
from client import Client


class ExtensionAutoResponsesSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        self._cooldowns: set
        super().__init__()

    async def cooldown(self, id: int, time: int) -> None: ...

    async def auto_response_handler(
        self, message: Message, args: ArgParser) -> None: ...
