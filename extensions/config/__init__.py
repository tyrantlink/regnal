from client import Client

def setup(client:Client) -> None:
	from .commands import config_commands

	client._extloaded()
	client.add_cog(config_commands(client))