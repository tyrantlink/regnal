from discord import AutoShardedBot
from .ClientBase import ClientBase
from utils.models import Project



class ClientLarge(ClientBase,AutoShardedBot):
	def __init__(self,project_data:Project) -> None:
		AutoShardedBot.__init__(self,command_prefix=None,help_command=None)
		ClientBase.__init__(self,project_data)