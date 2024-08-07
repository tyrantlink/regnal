from .subcog import ExtensionModMailSubCog
from .utils import new_modmail_message
from discord.ext.commands import Cog
from discord import Message
from re import sub, escape


class ExtensionModMailListeners(ExtensionModMailSubCog):
    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if (
            message.author.bot or
            not message.guild
        ):
            return

        guild_doc = await self.client.db.guild(message.guild.id)

        if not guild_doc.config.modmail.enabled:
            return

        modmail_id = guild_doc.data.modmail_threads.get(
            str(message.channel.id),
            None
        )

        if modmail_id is None:
            return

        modmail = await self.client.db.modmail(f'{message.guild.id}:{modmail_id}')

        if modmail.closed:
            return

        if not modmail.send_all and message.guild.me not in message.mentions:
            return

        await new_modmail_message(
            client=self.client,
            modmail_id=modmail.id,
            author=message.author,
            content=sub(
                f' ?{escape(message.guild.me.mention)} ?',
                '',
                message.content),
            timestamp=int(message.created_at.timestamp())
        )

        await self.client.helpers.notify_reaction(
            message,
            reaction='✅',
            delay=1 if modmail.send_all else 3
        )
