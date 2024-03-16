from .router import CrAPIRouter

class User(CrAPIRouter):
	async def reset_token(self,user_id:str) -> str:
		request = await self.session.post(f'/user/{user_id}/reset_token')
		match request.status:
			case 200: pass
			case 403: raise ValueError('invalid crapi token!')
			case 422: raise ValueError('invalid user_id!')
			case status: raise ValueError(f'unknown response code: {status}')

		return await request.json()