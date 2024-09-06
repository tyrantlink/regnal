from utils.pycord_classes import SubCog
from discord.ext.tasks import loop
from .models import Reminder
from client import Client


class ExtensionFunSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        self.bees_running: set
        self.pending_reminders: set[Reminder]
        super().__init__()

    @loop(seconds=1)
    async def reminder_loop(self) -> None: ...
