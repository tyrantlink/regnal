from utils.pycord_classes import SubCog
from .classes import MediaFixer
from discord import Message
from client import Client


class ExtensionMediaLinkFixerSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        super().__init__()
        self.embed_cache: dict[int, int]

    def fix(self, content: str) -> tuple[str | None, set[MediaFixer]]: ...
    async def wait_for_good_bot(self, message: Message) -> None: ...
