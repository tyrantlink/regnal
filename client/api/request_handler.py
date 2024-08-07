from discord.errors import InvalidData, Forbidden, NotFound, HTTPException
from utils.crapi.models import BaseGatewayMessage, Request, Response
from utils.crapi.enums import GatewayRequestType as Req
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


class RequestHandler:
    def __init__(self) -> None:
        self.client: 'Client'
        self.seq: int
        raise ValueError(
            'do not instantiate RequestHandler directly, use it as a subclass')

    async def gateway_send(self, message: BaseGatewayMessage) -> None: ...

    async def _handle_reload_au(self, message: Request) -> None:
        self.client.log.info('received reload_au request')

        await self.client.au.reload_au(use_cache=False)
        await self.gateway_send(Response(data={'success': True}))

    async def _handle_send_message_channel(self, message: Request) -> None:
        try:
            channel = (
                self.client.get_channel(int(message.data['channel'])) or
                await self.client.fetch_channel(int(message.data['channel'])))
        except (InvalidData, Forbidden, NotFound, HTTPException):
            channel = None

        if channel is None:
            await self.gateway_send(
                Response(data={'success': False, 'error': 'channel not found'}))
            return

        await channel.send(message.data['content'])

    async def _handle_send_message_user(self, message: Request) -> None:
        try:
            user = (
                self.client.get_user(int(message.data['user'])) or
                await self.client.fetch_user(int(message.data['user'])))
        except (NotFound, HTTPException):
            user = None

        if user is None:
            await self.gateway_send(
                Response(data={'success': False, 'error': 'user not found'}))
            return

        if not user.can_send():
            await self.gateway_send(
                Response(data={'success': False, 'error': 'cannot send message to user'}))
            return

        await user.send(message.data['content'])

    async def _handle_send_message(self, message: Request) -> None:
        self.client.log.info('received send_message request')

        channel = message.data.get('channel', None)
        user = message.data.get('user', None)

        if channel is None and user is None:
            await self.gateway_send(
                Response(data={'success': False, 'error': 'channel or user must be provided'}))
            return

        if channel is not None and user is not None:
            await self.gateway_send(
                Response(data={'success': False, 'error': 'only channel or user can be provided'}))
            return

        if channel is not None:
            await self._handle_send_message_channel(message)

        if user is not None:
            await self._handle_send_message_user(message)

        await self.gateway_send(Response(data={'success': True}))

    async def _handle_bot_info(self, message: Request) -> None:
        self.client.log.info('received bot_info request')

        await self.gateway_send(Response(data={
            'id': self.client.user.id,
            'name': self.client.user.name,
            'avatar': (self.client.user.avatar or self.client.user.default_avatar).url,
            'created_at': self.client.user.created_at.timestamp(),
            'guilds': [guild.id for guild in self.client.guilds]
        }))

    async def _handle_request(self, message: Request) -> None:
        match message.req:
            case Req.RELOAD_AU: await self._handle_reload_au(message)
            case Req.SEND_MESSAGE: await self._handle_send_message(message)
            case Req.BOT_INFO: await self._handle_bot_info(message)
