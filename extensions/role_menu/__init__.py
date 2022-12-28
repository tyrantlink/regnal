from client import Client

def setup(client:Client) -> None:
	from .commands import role_menu_commands

	client._extloaded()
	client.add_cog(role_menu_commands(client))