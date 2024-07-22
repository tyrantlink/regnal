from .listeners import ExtensionActivityRolesListeners
from .tasks import ExtensionActivityRolesTasks
from .logic import ExtensionActivityRolesLogic
from .config import register_config
from client import Client
from discord import Cog


class ExtensionActivityRoles(
    Cog,
    ExtensionActivityRolesTasks,
    ExtensionActivityRolesListeners,
    ExtensionActivityRolesLogic
):
    def __init__(self, client: Client) -> None:
        self.client = client


def setup(client: Client) -> None:
    client.permissions.register_permission('activity_roles.ignore')
    register_config(client.config)
    client.add_cog(ExtensionActivityRoles(client))
