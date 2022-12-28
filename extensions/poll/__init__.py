from client import Client

def setup(client:Client) -> None:
	from .commands import poll_commands

	client._extloaded()
	client.add_cog(poll_commands(client))