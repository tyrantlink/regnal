from discord import Bot
from .ClientBase import ClientBase
from utils.models import Project



class ClientSmall(ClientBase,Bot):
	def __init__(self,project_data:Project) -> None:
		Bot.__init__(self,command_prefix=None,help_command=None)
		ClientBase.__init__(self,project_data)
		self.shard_count