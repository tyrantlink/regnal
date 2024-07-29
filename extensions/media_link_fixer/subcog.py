from utils.pycord_classes import SubCog
from .classes import MediaFixer
from discord import Message
from client import Client


class ExtensionMediaLinkFixerSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        super().__init__()
        self.embed_cache: dict[int, int]

    def find_fixes(self, content: str) -> list[MediaFixer]: ...
    async def wait_for_good_bot(self, message: Message) -> None: ...
