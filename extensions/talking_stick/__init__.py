from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import talking_stick_commands

	client._extloaded()
	client.add_cog(talking_stick_commands(client))