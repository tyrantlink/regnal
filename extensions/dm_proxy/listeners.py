from utils.crapi.enums import GatewayRequestType as Req
from discord import Message, ChannelType, User, Webhook
from utils.tyrantlib import ArbitraryClass
from .subcog import ExtensionDmProxySubCog
from utils.crapi.models import Request
from discord.ext.commands import Cog
from aiohttp import ClientSession
from regex import match


class DumbSnowflake:
    def __init__(self, id: int) -> None:
        self.id = id


class ExtensionDMProxyListeners(ExtensionDmProxySubCog):
    async def get_bot_info(self, identifier: str) -> ArbitraryClass:
        if (bot_info := self.bot_info_cache.get(identifier, None)) is None:
            bot_info_data = await self.client.api.internal.get_bot_info(identifier)

            bot_info = ArbitraryClass(
                id=bot_info_data['id'],
                name=bot_info_data['name'],
                avatar=bot_info_data['avatar'],
                # created_at = bot_info_data['created_at'],
                # guilds = bot_info_data['guilds']
            )

            self.bot_info_cache[identifier] = bot_info

        return bot_info

    async def get_user_thread(self, user: User) -> int | None:
        user_doc = await self.client.db.user(user.id)

        if user_doc is None:
            return

        return user_doc.data.dm_threads.get(self.client.user.id, None)

    async def create_user_thread(self, author: User) -> int | None:
        async with ClientSession() as session:

            wh = Webhook.from_url(
                self.client.project.webhooks.dm_proxy, session=session
            )

            msg = await wh.send(
                wait=True,
                thread_name=f'{author.name} [{author.id}:{self.client.user.id}]',
                content=f'start of dm history between {author.mention} and {self.client.user.mention}'
            )

            user_doc = await self.client.db.user(author.id)

            if user_doc is None:
                return

            user_doc.data.dm_threads[str(self.client.user.id)] = msg.id
            await user_doc.save_changes()

        return msg.id

    async def handle_recieve(self, message: Message) -> None:
        user_doc = await self.client.db.user(message.author.id)

        if user_doc is None:
            return

        if (thread_id := user_doc.data.dm_threads.get(str(self.client.user.id), None)) is None:
            thread_id = await self.create_user_thread(message.author)

            if thread_id is None:
                return

        async with ClientSession() as session:
            wh = Webhook.from_url(
                self.client.project.webhooks.dm_proxy, session=session
            )

            await wh.send(
                wait=True,
                username=message.author.name,
                avatar_url=(
                    message.author.avatar or message.author.default_avatar).url,
                thread=DumbSnowflake(thread_id),
                content=f'{message.content}' if len(
                    message.content) <= 2000 else f'{message.content[:1997]}...',
                files=[await attachment.to_file() for attachment in message.attachments]
            )

    async def handle_send(self, message: Message) -> None:
        name_check = match(
            r'(.*) \[(\d+):(\d+)\]',
            str(message.channel.name)
        )

        if name_check is None:
            return

        user = name_check.group(2)
        forward = name_check.group(3)

        bot_info = await self.get_bot_info(forward)
        async with ClientSession() as session:
            wh = Webhook.from_url(
                self.client.project.webhooks.dm_proxy, session=session
            )

            await wh.send(
                wait=True,
                username=bot_info.name,
                avatar_url=bot_info.avatar,
                thread=message.channel,
                content=f'{message.content}' if len(
                    message.content) <= 2000 else f'{message.content[:1997]}...'
            )

        self.client.logging_ignore.add(message.id)
        await message.delete()

        await self.client.api.gateway_send(Request(
            req=Req.SEND_MESSAGE,
            forward=forward,
            data={
                'user': user,
                'content': (
                    f'{message.content}'
                    if len(message.content) <= 2000 else
                    f'{message.content[:1997]}...'
                )
            })
        )

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return

        if not (message.content or message.attachments):
            return

        match message.channel.type:
            case ChannelType.private:
                await self.handle_recieve(message)
            case ChannelType.public_thread if (
                    self.client.user.id == self.client.project.config.primary_bot_id and
                    message.channel.parent.id == self.client.project.config.dm_proxy_channel
            ):
                await self.handle_send(message)
