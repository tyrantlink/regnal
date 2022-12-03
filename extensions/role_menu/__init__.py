from main import client_cls

def setup(client:client_cls) -> None:
	from .commands import role_menu_commands

	client._extloaded()
	client.add_cog(role_menu_commands(client))