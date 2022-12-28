from client import Client

def setup(client:Client) -> None:
	from .commands import help_commands

	client._extloaded()
	client.add_cog(help_commands(client))