from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import qotd_commands

	client._extloaded()
	client.add_cog(qotd_commands(client))