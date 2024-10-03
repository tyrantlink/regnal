from .embeds import EditLogEmbed, DeleteLogEmbedFromMessage, DeleteLogEmbedFromID, MemberJoinLogEmbed, MemberLeaveLogEmbed, MemberBanLogEmbed, MemberUnbanLogEmbed
from discord import RawMessageUpdateEvent, RawMessageDeleteEvent, RawBulkMessageDeleteEvent, Embed, Member, User, Guild, Message
from .views import EditedLogView, DeletedLogView, BulkDeletedLogView
from .subcog import ExtensionLoggingSubCog
from discord.ext.commands import Cog


class ExtensionLoggingListeners(ExtensionLoggingSubCog):
    @Cog.listener()
    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent) -> None:
        if payload.guild_id is None:
            return

        log_channel = await self.get_logging_channel(payload.guild_id)

        if log_channel is None:
            return

        guild_doc = await self.client.db.guild(payload.guild_id)

        if not guild_doc.config.logging.edited_messages:
            return

        if payload.data.get('author', None) is None:
            return

        if int(payload.data['author']['id']) == self.client.user.id:
            return

        before = payload.cached_message
        after = await self.from_raw_edit(payload.data)

        if after is None:
            return

        if after.author.bot and not guild_doc.config.logging.log_bots:
            return

        if before is not None and before.content == after.content:
            return

        embed = EditLogEmbed(after, before)
        embeds = [embed, *embed.additional_embeds]
        multi_message = False
        view = EditedLogView(self.client)

        if sum([self.get_embed_length(embed) for embed in embeds]) > 6000:
            embeds = [embed]
            multi_message = True

        log_message = await log_channel.send(
            embeds=embeds,
            view=None if multi_message else view)

        if multi_message:
            for additional_embed in embed.additional_embeds:
                log_message = await log_message.reply(
                    embed=additional_embed,
                    view=(
                        view
                        if additional_embed == embed.additional_embeds[-1] else
                        None
                    ),
                    mention_author=False
                )

    @Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent) -> None:
        guild = self.client.get_guild(payload.guild_id)

        if guild is None:
            return

        if payload.message_id in self.client.logging_ignore:
            self.client.logging_ignore.discard(payload.message_id)
            return

        log_channel = await self.get_logging_channel(payload.guild_id)

        if log_channel is None:
            return

        guild_doc = await self.client.db.guild(payload.guild_id)

        if not guild_doc.config.logging.deleted_messages:
            return

        if (
            guild_doc.config.logging.pluralkit_support and
            (
                await self.deleted_by_pk(payload.message_id) or
                await self.deleted_by_plural(payload.message_id)
            )
        ):
            return

        if payload.cached_message is not None:
            if payload.cached_message.author.id == self.client.user.id:
                return

            if payload.cached_message.author.bot and not guild_doc.config.logging.log_bots:
                return

            deleter = await self.find_deleter_from_message(payload.cached_message)
            embed = DeleteLogEmbedFromMessage(payload.cached_message, deleter)

            await log_channel.send(
                embeds=[embed, *embed.additional_embeds],
                view=DeletedLogView(
                    self.client,
                    bool(payload.cached_message.attachments)
                )
            )

            return

        deleter, author = await self.find_deleter_from_id(payload.message_id, guild, payload.channel_id)

        if author is not None and author.id == self.client.user.id:
            return

        if author is not None and author.bot and not guild_doc.config.logging.log_bots:
            return

        await log_channel.send(
            embed=DeleteLogEmbedFromID(
                payload.message_id, payload.channel_id, author, deleter),
            view=DeletedLogView(self.client, False)
        )

    @Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: RawBulkMessageDeleteEvent) -> None:
        if payload.guild_id is None:
            return

        log_channel = await self.get_logging_channel(payload.guild_id)

        if log_channel is None:
            return

        if not (await self.client.db.guild(payload.guild_id)).config.logging.deleted_messages:
            return

        embed = Embed(
            title=f'{len(payload.message_ids)} messages bulk deleted in <#{payload.channel_id}>',
            color=0xff6969
        )
        message_ids = ','.join([str(i) for i in payload.message_ids])

        if len(message_ids) <= 4096:
            embed.description = message_ids
            await log_channel.send(embed=embed, view=BulkDeletedLogView(self.client))
            return

        if len(message_ids) > 256000:
            embed.description = 'there\'s actually just too many i can\'t >.<'
            await log_channel.send(embed=embed, view=BulkDeletedLogView(self.client))
            return

        tmp_value = str(payload.message_ids[0])
        index = 1

        for msg_id in payload.message_ids:
            if len(tmp_value)+len(str(msg_id)) > 1023:
                embed.add_field(
                    name=f'message IDs - part {index}', value=tmp_value, inline=False
                )

                tmp_value = str(msg_id)
                continue
            tmp_value += f',{msg_id}'

        for field in embed.fields:
            field.name += f'/{index}'

        await log_channel.send(embed=embed, view=BulkDeletedLogView(self.client))

    @Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        guild_doc = await self.client.db.guild(member.guild.id)

        if not guild_doc.config.logging.member_join:
            return

        log_channel = await self.get_logging_channel(member.guild.id)

        if log_channel is None:
            return

        await log_channel.send(embed=MemberJoinLogEmbed(member))

    @Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        guild_doc = await self.client.db.guild(member.guild.id)

        if not guild_doc.config.logging.member_leave:
            return

        log_channel = await self.get_logging_channel(member.guild.id)

        if log_channel is None:
            return

        await log_channel.send(embed=MemberLeaveLogEmbed(member))

    @Cog.listener()
    async def on_member_ban(self, guild: Guild, member: User) -> None:
        guild_doc = await self.client.db.guild(guild.id)

        if not guild_doc.config.logging.member_ban:
            return

        log_channel = await self.get_logging_channel(guild.id)

        if log_channel is None:
            return

        await log_channel.send(
            embed=MemberBanLogEmbed(
                member,
                await self.find_ban_entry(guild, member.id))
        )

    @Cog.listener()
    async def on_member_unban(self, guild: Guild, member: User) -> None:
        guild_doc = await self.client.db.guild(guild.id)

        if not guild_doc.config.logging.member_unban:
            return

        log_channel = await self.get_logging_channel(guild.id)

        if log_channel is None:
            return

        await log_channel.send(
            embed=MemberUnbanLogEmbed(
                member,
                await self.find_ban_entry(guild, member.id, True))
        )

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if not (
            message.author.id == self.client.user.id and
            message.content == ''
        ):
            return

        self.false_logs.add(message.id)
