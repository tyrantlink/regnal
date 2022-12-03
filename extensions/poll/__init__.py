from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import poll_commands

	client._extloaded()
	client.add_cog(poll_commands(client))