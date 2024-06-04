from .subcog import ExtensionActivityRolesSubCog
from discord import Cog


class ExtensionActivityRolesListeners(ExtensionActivityRolesSubCog):
	@Cog.listener()
	async def on_ready(self) -> None:
		if not self.activity_roles_loop.is_running():
			self.activity_roles_loop.start()