from main import client_cls


def setup(client:client_cls) -> None:
	from .listeners import auto_response_listeners

	client._extloaded()
	client.add_cog(auto_response_listeners(client))