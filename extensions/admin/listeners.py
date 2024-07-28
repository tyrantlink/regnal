from discord.errors import Forbidden, NotFound, HTTPException
from .subcog import ExtensionAdminSubCog
from discord.ext.commands import Cog
from discord import Message, Embed
from .views import AntiScamBotView
from datetime import timedelta


class ExtensionAdminListeners(ExtensionAdminSubCog):
    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if not message.guild:
            return

        guild_doc = await self.client.db.guild(message.guild.id)

        if guild_doc is None:
            return

        if not guild_doc.config.general.anti_scam_bot:
            return

        self.recent_messages.append(message)

        self.recent_messages = list(filter(
            lambda m: m.created_at > message.created_at -
            timedelta(seconds=15),
            self.recent_messages)
        )

        duplicate_messages = list(filter(
            lambda m: m.author == message.author and m.content == message.content,
            self.recent_messages)
        )

        if len(duplicate_messages) < 3:
            return

        channels = {m.channel for m in duplicate_messages}

        # ? probably not necessary to filter by ids, but just in case
        if len({c.id for c in channels}) < 3:
            return

        warnings: list[str] = []

        try:
            await message.author.timeout_for(timedelta(minutes=10), reason='anti scam bot protection')
        except (Forbidden, HTTPException):
            warnings.append('failed to timeout user')

        for message in duplicate_messages:
            try:
                await message.delete(reason='anti scam bot protection')
            except (Forbidden, NotFound, HTTPException):
                warnings.append(
                    f'failed to delete message in {message.channel.mention}'
                )

        if guild_doc.config.logging.channel is None:
            return

        logging_channel = message.guild.get_channel(
            guild_doc.config.logging.channel
        )

        if logging_channel is None:
            return

        embed = Embed(
            title='anti scam bot protection',
            description=f'{message.author.mention} has sent the same message in three different channels in quick succession',
            color=0xff6969
        )
        embed.add_field(
            name='message',
            value=message.content if len(
                message.content) < 1024 else f'{message.content[:1021]}...',
            inline=False
        )
        embed.add_field(
            name='channels',
            value='\n'.join(c.mention for c in channels),
            inline=False
        )
        if warnings:
            embed.add_field(
                name='warnings',
                value='\n'.join(warnings),
                inline=False
            )
        embed.set_footer(text=str(message.author.id))

        content = None
        if guild_doc.config.general.moderator_role is not None:
            role = message.guild.get_role(
                guild_doc.config.general.moderator_role
            )
            if role is not None:
                content = role.mention

        await logging_channel.send(
            content=content,
            embed=embed,
            view=AntiScamBotView(self.client)
        )
