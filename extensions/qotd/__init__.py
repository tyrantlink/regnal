from utils.db.documents import Guild as GuildDocument
from .listeners import ExtensionQOTDListeners
from .commands import ExtensionQOTDCommands
from .config import subcategories, options
from .logic import ExtensionQOTDLogic
from .tasks import ExtensionQOTDTasks
from discord.ext.commands import Cog
from .views import QOTDAskLog
from .models import QOTDPack
from discord import Guild
from client import Client


class ExtensionQOTD(
    Cog,
    ExtensionQOTDLogic,
    ExtensionQOTDListeners,
    ExtensionQOTDTasks,
    ExtensionQOTDCommands
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.recently_asked = set()
        self.packs: dict[str, QOTDPack] = {}
        self._guilds: tuple[int,
                            list[tuple[Guild, GuildDocument]]] = (0, set())
        self._rescan = False
        self.client.add_view(QOTDAskLog(self.client))


def setup(client: Client) -> None:
    client.permissions.register_permission('qotd.remove_custom')
    client.config._subcategories += subcategories
    client.config._options += options
    client.add_cog(ExtensionQOTD(client))
