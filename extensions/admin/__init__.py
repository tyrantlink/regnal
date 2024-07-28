from .listeners import ExtensionAdminListeners
from .commands import ExtensionAdminCommands
from .config import register_config
from .views import AntiScamBotView
from discord import Cog, Message
from client import Client


class ExtensionAdmin(
    Cog,
    ExtensionAdminCommands,
    ExtensionAdminListeners
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.recent_messages: list[Message] = []
        self.client.add_view(AntiScamBotView(self.client))


def setup(client: Client) -> None:
    client.add_cog(ExtensionAdmin(client))
    register_config(client.config)
    client.permissions.register_permission('admin.ban_user')
    client.permissions.register_permission('admin.untimeout_user')
