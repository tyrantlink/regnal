from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import commands_commands

	client._extloaded()
	client.add_cog(commands_commands(client))