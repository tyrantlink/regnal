
from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import fun_commands

	client._extloaded()
	client.add_cog(fun_commands(client))