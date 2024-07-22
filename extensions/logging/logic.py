from discord import Message, Member, TextChannel, Guild, AuditLogEntry, Embed
from .subcog import ExtensionLoggingSubCog
from datetime import datetime, timedelta
from aiohttp import ClientSession
from asyncio import sleep


class ExtensionLoggingLogic(ExtensionLoggingSubCog):
    async def get_logging_channel(self, guild_id: int) -> TextChannel | None:
        if (guild := self.client.get_guild(guild_id)) is None:
            return None

        logging_config = (await self.client.db.guild(guild.id)).config.logging

        if logging_config.enabled is False:
            return None

        if logging_config.channel is None:
            return None

        return (
            guild.get_channel(logging_config.channel) or
            await guild.fetch_channel(logging_config.channel)
        )

    async def from_raw_edit(self, data: dict) -> Message | None:
        _guild = self.client.get_guild(data.get('guild_id')) or await self.client.fetch_guild(data.get('guild_id'))
        _channel = _guild.get_channel(data.get('channel_id')) or await _guild.fetch_channel(data.get('channel_id'))
        message = self.client.get_message(data.get('id')) or await _channel.fetch_message(data.get('id'))

        if message is None:
            return None

        message.content = data.get('content')
        ts = data.get('edited_timestamp')

        message._edited_timestamp = \
            datetime.fromisoformat(ts) if ts is not None else None

        return message

    async def find_deleter_from_message(self, message: Message) -> Member:
        if message.guild.me.guild_permissions.view_audit_log is False:
            return None

        async for log in message.guild.audit_logs(after=datetime.now()-timedelta(minutes=5), oldest_first=False):
            if (
                    log.action.name == 'message_delete' and
                    log.target.id == message.author.id and
                    log.extra.channel.id == message.channel.id and
                    log.extra.count <= self.cached_counts.get(
                        f'{message.channel.id}{log.target.id}', log.extra.count-1)+1
            ):
                self.cached_counts.update(
                    {f'{message.channel.id}{log.target.id}': log.extra.count}
                )

                return log.user

        if message.id in self.client.recently_deleted:
            self.client.recently_deleted.discard(message.id)
            return message.guild.me

        return message.author

    async def find_deleter_from_id(self, message_id: int, guild: Guild, channel_id: int) -> tuple[Member, Member] | tuple[None, None]:
        if guild.me.guild_permissions.view_audit_log is False:
            return None

        async for log in guild.audit_logs(after=datetime.now()-timedelta(minutes=5), oldest_first=False):
            if (
                    log.action.name == 'message_delete' and
                    log.extra.channel.id == channel_id and
                    log.extra.count <= self.cached_counts.get(
                        f'{channel_id}{log.target.id}', log.extra.count-1)+1
            ):
                self.cached_counts.update(
                    {f'{channel_id}{log.target.id}': log.extra.count}
                )

                return log.user, log.target

        if message_id in self.client.recently_deleted:
            self.client.recently_deleted.discard(message_id.id)

        return None, None

    async def find_ban_entry(self, guild: Guild, user_id: int, unban: bool = False) -> AuditLogEntry | None:
        if guild.me.guild_permissions.view_audit_log is False:
            return None

        async for log in guild.audit_logs(after=datetime.now()-timedelta(minutes=5), oldest_first=False):
            if (
                    log.action.name == 'unban' if unban else 'ban' and
                    log.target.id == user_id and
                    datetime.now().timestamp()-log.created_at.timestamp() < 300
            ):
                return log

        return None

    async def deleted_by_pk(self, message_id: int, delay: int | None = None, recurse_count: int | None = None) -> bool:
        if (recurse_count or 0) > 5:
            return False

        if delay:
            await sleep(delay)

        async with ClientSession(
                base_url='https://api.pluralkit.me',
                headers={
                    'Authorization': self.client.project.config.pluralkit_token,
                    'User-Agent': f'{self.client.user.display_name} Discord Bot/{self.client.version.semantic} (contact: {self.client.project.config.contact_email})'
                }
        ) as session:
            try:
                async with session.get(f'/v2/messages/{message_id}') as response:
                    match response.status:
                        case 200:
                            return True
                        case 404:
                            return False
                        case 429:
                            return await self.deleted_by_pk(
                                message_id=message_id,
                                delay=(await response.json()).get('retry_after', 2000)/1000+250,
                                recurse_count=(recurse_count or 0)+1
                            )
                        case _:
                            return False
            except TimeoutError:  # ? pk api is down
                return False

    def get_embed_length(self, embed: Embed) -> int:
        return sum([
            len(embed.title if embed.title else ''),
            len(embed.description if embed.description else ''),
            sum([len(field.name)+len(field.value) for field in embed.fields]),
            len(embed.footer.text if embed.footer else ''),
            len(embed.author.name if embed.author else '')]
        )
