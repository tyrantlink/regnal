from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import cryptography_commands

	client._extloaded()
	client.add_cog(cryptography_commands(client))