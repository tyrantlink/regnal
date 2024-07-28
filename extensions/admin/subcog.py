from utils.pycord_classes import SubCog
from discord import Message
from client import Client


class ExtensionAdminSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        self.recent_messages: list[Message]
        super().__init__()
