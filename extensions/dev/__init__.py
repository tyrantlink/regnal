from client import Client

def setup(client:Client) -> None:
	from .commands import dev_commands

	client._extloaded()
	client.add_cog(dev_commands(client))