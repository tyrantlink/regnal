from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import help_commands

	client._extloaded()
	client.add_cog(help_commands(client))