from discord.errors import NotFound, Forbidden, HTTPException
from discord import Message, RawReactionActionEvent
from .subcog import ExtensionMediaLinkFixerSubCog
from asyncio import sleep, create_task
from discord.ext.commands import Cog
from regex import sub, findall


class ExtensionMediaLinkFixerListeners(ExtensionMediaLinkFixerSubCog):
    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.guild is None:
            return

        if any((
            message.author.bot,
            message.flags.suppress_embeds,
            not message.channel.can_send()
        )):
            return

        guild_doc = await self.client.db.guild(message.guild.id)

        if not guild_doc.config.general.replace_media_links:
            return

        user_doc = await self.client.db.user(message.author.id)

        if (
            user_doc is not None and
            user_doc.config.general.disable_media_link_replacement
        ):
            return

        fix_message, used_fixes = self.fix(message.content)
        if fix_message is None or not used_fixes:
            return

        if any((fix.clear_embeds for fix in used_fixes)):
            await sleep(1)
            await message.edit(suppress=True)

        self_message = await message.reply(fix_message, mention_author=False)
        self.embed_cache[message.id] = self_message.id

        good_bot_task = create_task(self.wait_for_good_bot(self_message))

        await sleep(max((fix.wait_time for fix in used_fixes)))

        try:
            self_message = await self_message.channel.fetch_message(self_message.id)
        except NotFound:
            return

        if self_message.embeds:
            return

        await message.edit(suppress=False)
        await self_message.delete()
        good_bot_task.cancel()
        del self.embed_cache[message.id]

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent) -> None:
        if (
            payload.user_id == self.client.user.id or
            payload.guild_id is None or
            payload.emoji.name != '❌'
        ):
            return
        message = (
            self.client.get_message(payload.message_id) or
            await self.client.get_guild(
                payload.guild_id
            ).get_channel(
                payload.channel_id
            ).fetch_message(payload.message_id)
        )

        if message is None:
            return

        if message.author.id != self.client.user.id:
            return

        if message.reference is None:
            return

        if not message.content.startswith('links converted to embed friendly urls:'):
            return

        reference = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)

        if reference is None:
            return

        reactor = message.guild.get_member(payload.user_id) or await message.guild.fetch_member(payload.user_id)

        if (
            reference.author.id == payload.user_id or
            (
                message.channel.permissions_for(reactor).manage_messages
                if reactor else
                False
            )
        ):
            await message.delete()
            await reference.edit(suppress=False)

    @Cog.listener()
    async def on_message_delete(self, message: Message) -> None:
        if message.guild is None:
            return

        if message.author.id == self.client.user.id:
            if not message.content.startswith('links converted to embed friendly urls:'):
                return

            reference = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)
            if reference is None:
                return

            try:
                await reference.edit(suppress=False)
            except NotFound:
                pass

        if message.id in self.embed_cache:
            try:
                self_message = await message.channel.fetch_message(
                    self.embed_cache[message.id]
                )
            except (NotFound, Forbidden, HTTPException):
                return
            await self_message.delete()
            del self.embed_cache[message.id]
