from main import client_cls


def setup(client:client_cls) -> None:
	from .commands import admin_commands

	client._extloaded()
	client.add_cog(admin_commands(client))