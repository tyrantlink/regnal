from .listeners import ExtensionAutoResponsesListeners
from .commands import ExtensionAutoResponsesCommands
from .logic import ExtensionAutoResponsesLogic
from .config import register_config
from .classes import AutoResponses
from client import Client
from discord import Cog


class ExtensionAutoResponses(Cog,
	ExtensionAutoResponsesLogic,
	ExtensionAutoResponsesListeners,
	ExtensionAutoResponsesCommands
):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.client.au = AutoResponses(client)
		self._cooldowns = set()

def setup(client:Client) -> None:
	client.permissions.register_permission('auto_responses.custom')
	client.permissions.register_permission('auto_responses.overrides')
	register_config(client.config)
	client.add_cog(ExtensionAutoResponses(client))