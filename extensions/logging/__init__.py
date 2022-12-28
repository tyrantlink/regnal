from client import Client

def setup(client:Client) -> None:
	from .listeners import logging_listeners
	from .commands import logging_commands

	client._extloaded()
	client.add_cog(logging_listeners(client))
	client.add_cog(logging_commands(client))