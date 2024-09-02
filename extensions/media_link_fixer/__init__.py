from .listeners import ExtensionMediaLinkFixerListeners
from .logic import ExtensionMediaLinkFixerLogic
from .config import options
from client import Client
from discord import Cog


class ExtensionMediaLinkFixer(
    Cog,
    ExtensionMediaLinkFixerListeners,
    ExtensionMediaLinkFixerLogic
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.embed_cache = {}


def setup(client: Client) -> None:
    client.config._options += options
    client.add_cog(ExtensionMediaLinkFixer(client))
