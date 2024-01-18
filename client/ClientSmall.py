from .ClientBase import ClientBase
from utils.models import Project
from discord import Bot,Intents


class ClientSmall(ClientBase,Bot):
	def __init__(self,project_data:Project) -> None:
		Bot.__init__(self,command_prefix=None,help_command=None,intents=Intents.all(),max_messages=100000)
		ClientBase.__init__(self,project_data)