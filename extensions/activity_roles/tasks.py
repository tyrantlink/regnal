from .subcog import ExtensionActivityRolesSubCog
from discord.ext.tasks import loop
from datetime import time


class ExtensionActivityRolesTasks(ExtensionActivityRolesSubCog):
    @loop(time=[time(h, m) for h in range(0, 24) for m in [0, 30]])
    async def activity_roles_loop(self) -> None:
        await self.client._ready.wait()

        for guild in self.client.guilds:
            changes = await self.new_day(guild)

            if changes is not None:
                await self.log_changes(guild, changes)
