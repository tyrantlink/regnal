from utils.tyrantlib import ArbitraryClass
from utils.pycord_classes import SubCog
from discord import User, Message
from client import Client


class ExtensionDmProxySubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        self.bot_info_cache: dict
        super().__init__()

    async def get_bot_info(self, identifier: str) -> ArbitraryClass: ...
    async def get_user_thread(self, user: User) -> int | None: ...
    async def create_user_thread(self, author: User) -> int | None: ...
    async def handle_recieve(self, message: Message) -> None: ...
    async def handle_send(self, message: Message) -> None: ...
