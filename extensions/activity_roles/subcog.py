from utils.pycord_classes import SubCog
from .models import ActivityRoleChanges
from discord.ext.tasks import loop
from datetime import time
from discord import Guild
from client import Client


class ExtensionActivityRolesSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        super().__init__()

    async def new_day(self, guild: Guild) -> ActivityRoleChanges: ...
    async def log_changes(self, guild: Guild,
                          changes: ActivityRoleChanges) -> None: ...

    @loop(time=[time(h, m) for h in range(0, 24) for m in [0, 30]])
    async def activity_roles_loop(self) -> None: ...
