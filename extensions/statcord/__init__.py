from main import client_cls

def setup(client:client_cls) -> None:
	from .listeners import statcord_listeners

	client._extloaded()
	client.add_cog(statcord_listeners(client))