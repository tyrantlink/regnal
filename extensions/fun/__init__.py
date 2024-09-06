from .listeners import ExtensionFunListeners
from .commands import ExtensionFunCommands
from discord.ext.commands import Cog
from .tasks import ExtensionFunTasks
from client import Client


class ExtensionFun(
    Cog,
    ExtensionFunCommands,
    ExtensionFunListeners,
    ExtensionFunTasks
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.bees_running = set()
        self.pending_reminders = set()


def setup(client: Client) -> None:
    client.add_cog(ExtensionFun(client))
