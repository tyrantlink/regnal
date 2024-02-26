from utils.crapi.models import BaseGatewayMessage,Request,Heartbeat
from utils.crapi.enums import GatewayOpCode as Op,GatewayRequestType as Req
if not 'TYPE_HINT': from client import Client
from aiohttp import ClientSession,WSMsgType
from asyncio import create_task,sleep
from .message_handler import MessageHandler
from random import random


class CrAPI(MessageHandler):
	def __init__(self,client:'Client') -> None:
		self.client = client
		self.base_url = self.client.project.api.url
		self.token = self.client.project.bot.api_token
		self.session = ClientSession(self.base_url,headers={'token':self.token})
		self.gateway_ws = None
		self.seq = 0

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

	async def create_masked_au_url(self,au_id:str) -> str:
		request = await self.session.post(f'/au/{au_id}/masked_url')
		match request.status:
			case 200: pass
			case 403: raise ValueError('invalid crapi token!')
			case 422: raise ValueError('invalid au_id!')
			case status:
				try: json = await request.json()
				except Exception: json = {}
				raise ValueError(f'unknown response code: {status} | {json.get("detail","")}')

		return await request.json()

	async def reset_user_token(self,user_id:int) -> str:
		request = await self.session.post(f'/user/{user_id}/reset_token')
		match request.status:
			case 200: pass
			case 403: raise ValueError('invalid crapi token!')
			case 422: raise ValueError('invalid user_id!')
			case status: raise ValueError(f'unknown response code: {status}')

		return await request.json()