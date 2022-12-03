from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import config_commands

	client._extloaded()
	client.add_cog(config_commands(client))