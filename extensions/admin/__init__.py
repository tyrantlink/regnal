from .commands import ExtensionAdminCommands
from client import Client
from discord import Cog


class ExtensionAdmin(
    Cog,
    ExtensionAdminCommands
):
    def __init__(self, client: Client) -> None:
        self.client = client


def setup(client: Client) -> None:
    client.add_cog(ExtensionAdmin(client))
