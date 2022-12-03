from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import sauce_commands

	client._extloaded()
	client.add_cog(sauce_commands(client))