from .subcog import ExtensionFunSubCog
from discord.ext.tasks import loop
from time import time


class ExtensionFunTasks(ExtensionFunSubCog):
    @loop(seconds=1)
    async def reminder_loop(self) -> None:
        if not self.client.is_ready():
            return

        for reminder in self.pending_reminders.copy():
            if reminder.trigger_time <= time():
                await reminder.user.send(
                    f'you asked me to remind you: {reminder.reminder}'
                )
                self.pending_reminders.discard(reminder)
