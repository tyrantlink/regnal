from utils.db.documents import Guild as GuildDocument
from .listeners import ExtensionTalkingStickListeners
from .logic import ExtensionTalkingStickLogic
from .tasks import ExtensionTalkingStickTasks
from .config import subcategories, options
from discord.ext.commands import Cog
from discord import Guild
from client import Client


class ExtensionTalkingStick(
    Cog,
    ExtensionTalkingStickLogic,
    ExtensionTalkingStickListeners,
    ExtensionTalkingStickTasks
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.recently_rolled = set()
        self._guilds: tuple[int, list[tuple[Guild, GuildDocument]]] = (0, [])
        self._rescan = False


def setup(client: Client) -> None:
    client.config._subcategories += subcategories
    client.config._options += options
    client.add_cog(ExtensionTalkingStick(client))
