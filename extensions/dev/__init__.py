
from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import dev_commands

	client._extloaded()
	client.add_cog(dev_commands(client))