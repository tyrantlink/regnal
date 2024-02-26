from utils.crapi.models import BaseGatewayMessage,Request,Ack
from utils.crapi.enums import GatewayOpCode as Op
if not 'TYPE_HINT': from client import Client
from .request_handler import RequestHandler

class MessageHandler(RequestHandler):
	def __init__(self) -> None:
		self.client:'Client'
		self.seq:int
		raise ValueError('do not instantiate MessageHandler directly, use it as a subclass')

	async def gateway_send(self,message:BaseGatewayMessage) -> None: ...
	def inc_seq(self) -> None: ...

	async def _message_handler(self,message:dict) -> None:
		self.inc_seq()
		match Op(message['op']):
			case Op.ACK: await self._handle_ack(Ack.model_validate(message))
			case Op.REQUEST: await self._handle_request(Request.model_validate(message))

	async def _handle_ack(self,message:Ack) -> None:
		if message.seq != self.seq:
			await self.disconnect(f'invalid sequence number: {message.seq} | expected: {self.seq}')