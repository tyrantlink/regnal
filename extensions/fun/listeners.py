from .subcog import ExtensionFunSubCog
from asyncio import create_task, sleep
from discord.ext.commands import Cog
from discord import Message


class ExtensionFunListeners(ExtensionFunSubCog):
    async def remove_good_bot_response(self, message_id: int) -> None:
        await sleep(61)
        self.recent_good_bot_responses.remove(message_id)

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if any((
            message.guild is None,
            message.author != self.client.user,
            message.id in self.recent_good_bot_responses
        )):
            return
        
        try:
            response:Message = await self.client.wait_for(
                'message',
                check=lambda m: (
                    'good bot' in m.content.lower()
                ),
                timeout=60
            )
        except TimeoutError:
            return
        
        if message.id in self.recent_good_bot_responses:
            return

        # ? i'm so good at variable names
        response_response = await response.reply(
            '<:cutesmile:1118502809772494899>',
            mention_author=False
        )

        self.recent_good_bot_responses.add(response_response.id)
        create_task(self.remove_good_bot_response(response_response.id))

