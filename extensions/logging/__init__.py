from .views import EditedLogView, DeletedLogView, BulkDeletedLogView
from .listeners import ExtensionLoggingListeners
from .logic import ExtensionLoggingLogic
from discord.ext.commands import Cog
from .config import register_config
from client import Client


class ExtensionLogging(
    Cog,
    ExtensionLoggingLogic,
    ExtensionLoggingListeners
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.client.logging_ignore = set()
        register_config(self.client.config)
        self.client.add_view(EditedLogView(self.client))
        self.client.add_view(DeletedLogView(self.client))
        self.client.add_view(BulkDeletedLogView(self.client))
        self.cached_counts = {}


def setup(client: Client) -> None:
    client.permissions.register_permission('logging.clear_logs')
    client.permissions.register_permission('logging.hide_attachments')
    client.add_cog(ExtensionLogging(client))
