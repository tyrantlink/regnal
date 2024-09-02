from .listeners import ExtensionActivityRolesListeners
from .tasks import ExtensionActivityRolesTasks
from .logic import ExtensionActivityRolesLogic
from .config import subcategories, options
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
    client.config._subcategories += subcategories
    client.config._options += options
    client.add_cog(ExtensionActivityRoles(client))
