from aiohttp import ClientSession
from asyncio import create_task
from datetime import datetime
from base64 import b64encode
from json import dumps


class Logger:
	def __init__(self,url:str,token:str) -> None:
		self.url = url
		self.headers = {
			"Authorization": f"Basic {token}",
			"Content-Type": "application/json"}
	
	async def logstream_init(self) -> None:
		async with ClientSession() as session:
			base_url,logstream = '/'.join(self.url.split('/')[:-1]),self.url.split('/')[-1]
			logstreams = [d['name'] for d in await (await session.get(base_url,headers=self.headers)).json()]
			if logstream not in logstreams:
				async with session.put(self.url,headers=self.headers) as resp:
					if resp.status != 200:
						raise Exception(f'Logger failed with status {resp.status}\n{await resp.text()}')


	async def _log(self,message:str,label:str,guild_id:int|None=None,metadata:dict|None=None) -> None:
		print(f'[{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}] [{label}] {message}')
		headers = {
			**self.headers,
			f'X-P-Tag-label':label,
			f'X-P-Tag-guild_id':str(guild_id).lower(),
			**{f'X-P-Meta-{k}':str(v) for k,v in (metadata or {}).items()}}

		async with ClientSession() as session:
			async with session.post(self.url,headers=headers,data=dumps([{'label':label,'message':message}])) as resp:
				if resp.status != 200:
					raise Exception(f'Logger failed with status {resp.status}\n{await resp.text()}')

	def custom(self,label:str,message:str,guild_id:int|None=None,**metadata) -> None: create_task(self._log(message,label.upper(),guild_id,metadata))
	def info(self,message:str,guild_id:int|None=None,**metadata)             -> None: self.custom('info',message,guild_id,**metadata)
	def error(self,message:str,guild_id:int|None=None,**metadata)            -> None: self.custom('error',message,guild_id,**metadata)
	def warning(self,message:str,guild_id:int|None=None,**metadata)          -> None: self.custom('warning',message,guild_id,**metadata)
	def debug(self,message:str,guild_id:int|None=None,**metadata)            -> None: self.custom('debug',message,guild_id,**metadata)
	def critical(self,message:str,guild_id:int|None=None,**metadata)         -> None: self.custom('critical',message,guild_id,**metadata)

	def success(self,message:str,guild_id:int|None=None,**metadata)          -> None: self.custom('success',message,guild_id,**metadata)
	def client_error(self,message:str,guild_id:int|None=None,**metadata)     -> None: self.custom('client_error',message,guild_id,**metadata)
	def server_error(self,message:str,guild_id:int|None=None,**metadata)     -> None: self.custom('server_error',message,guild_id,**metadata)
