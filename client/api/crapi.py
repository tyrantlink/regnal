from utils.crapi.models import BaseGatewayMessage,Heartbeat
from .routers import AutoResponses,User,Internal
if not 'TYPE_HINT': from client import Client
from .message_handler import MessageHandler
from aiohttp import ClientSession,WSMsgType
from asyncio import create_task,sleep
from random import random


class CrAPI(MessageHandler):
	def __init__(self,client:'Client') -> None:
		self.client = client
		self.base_url = self.client.project.api.url
		self.token = self.client.project.bot.api_token
		self.session = ClientSession(self.base_url,headers={'token':self.token})
		self.gateway_ws = None
		self.seq = 0

		self.au = AutoResponses(self)
		self.user = User(self)
		self.internal = Internal(self)

	@property
	def is_connected(self) -> bool:
		return self.gateway_ws and not self.gateway_ws.closed

	def inc_seq(self) -> None:
		self.seq += 1
		if self.seq == 8192: self.seq = 0

	async def connect(self,reconnect:bool=True) -> None:
		self.gateway_ws = await self.session.ws_connect('/i/gateway')
		self.seq = 0
		create_task(self._gateway_receive())
		create_task(self._heartbeat())
		self.client.log.info('connected to crAPI')
		if reconnect: create_task(self._reconnection_handler())

	async def disconnect(self,message:str='no reason') -> None:
		self.client.log.info(f'disconnected from crAPI: {message}')
		if not self.is_connected: return
		await self.gateway_ws.close(message=message.encode())

	async def _gateway_receive(self) -> BaseGatewayMessage:
		while self.is_connected:
			message = await self.gateway_ws.receive()
			match message.type:
				case WSMsgType.TEXT: await self._message_handler(message.json())
				case WSMsgType.CLOSE|WSMsgType.CLOSED|WSMsgType.CLOSING:
					await self.disconnect(message.extra or 'no reason')
				case _: print(f'unknown message type: {message.type} | {message.extra}')

	async def _heartbeat(self) -> None:
		while True:
			await sleep(30+29*random())
			if not self.is_connected: break
			self.client.log.debug(f'sending crAPI heartbeat seq {self.seq}')
			try: await self.gateway_send(Heartbeat())
			except ValueError: break

	async def gateway_send(self,message:BaseGatewayMessage) -> None:
		if not self.is_connected: raise ValueError('not connected to crAPI gateway!')
		self.inc_seq()
		message.seq = self.seq
		await self.gateway_ws.send_str(message.model_dump_json())

	async def _reconnection_handler(self) -> None:
		while True:
			await sleep(5)
			if self.is_connected: continue
			self.client.log.debug('attempting to reconnect to crAPI')
			try: await self.connect()
			except Exception: continue
			break