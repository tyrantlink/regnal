from aiohttp import ClientSession



class CrAPI:
	def __init__(self,base_url:str,token:str) -> None:
		self.base_url = base_url
		self.token = token
		self.session = ClientSession(base_url,headers={'token':token})

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