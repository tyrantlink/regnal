from .listeners import ExtensionAutoResponsesListeners
from .commands import ExtensionAutoResponsesCommands
from .logic import ExtensionAutoResponsesLogic
from .config import subcategories, options
from au_scripts.aulib import SECRETS
from .classes import AutoResponses
from client import Client
from discord import Cog


class ExtensionAutoResponses(
    Cog,
    ExtensionAutoResponsesLogic,
    ExtensionAutoResponsesListeners,
    ExtensionAutoResponsesCommands
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.client.au = AutoResponses(client)
        self._cooldowns = set()


def setup(client: Client) -> None:
    client.permissions.register_permission('auto_responses.custom')
    client.permissions.register_permission('auto_responses.override')
    client.config._subcategories += subcategories
    client.config._options += options

    client.add_cog(ExtensionAutoResponses(client))

    loaded_secrets = ", ".join(
        k for k, v
        in SECRETS.__dict__.items()
        if v is not None
    )

    client.log.info(f'loaded au_script secrets: {loaded_secrets}')
