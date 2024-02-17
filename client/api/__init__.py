if not 'TYPE_HINT': from client import Client
from aiohttp import ClientSession


class CrAPI:
	def __init__(self,client:'Client') -> None:
		self.client = client
		self.base_url = self.client.project.api.url
		self.token = self.client.project.api.token
		self.session = ClientSession(self.base_url,headers={'token':self.token})
		self._connected = False
	
	@property
	def is_connected(self) -> bool:
		return self._connected

	async def connect(self) -> None:
		... # do this when the gateway exists in crapi

	async def create_masked_au_url(self,au_id:str) -> str:
		request = await self.session.post(f'/au/{au_id}/masked_url')
		match request.status:
			case 200: pass
			case 403: raise ValueError('invalid crapi token!')
			case 422: raise ValueError('invalid au_id!')
			case status: raise ValueError(f'unknown response code: {status}')

		return await request.json()

	async def reset_user_token(self,user_id:int) -> str:
		request = await self.session.post(f'/user/{user_id}/reset_token')
		match request.status:
			case 200: pass
			case 403: raise ValueError('invalid crapi token!')
			case 422: raise ValueError('invalid user_id!')
			case status: raise ValueError(f'unknown response code: {status}')

		return await request.json()