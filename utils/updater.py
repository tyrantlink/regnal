from asyncio import create_subprocess_shell,sleep
from discord import Activity,ActivityType
from os.path import exists
from client import Client
from time import time
from os import _exit


class UpdateHandler:
	def __init__(self,client:Client,payload:dict) -> None:
		self.client = client
		self.payload = payload
		self.commits:list[dict] = payload.get('commits',[])
		self.actions:set[str] = set()

	async def run(self) -> None:
		self.client.log.log('update',f'update detected...',to_db=False)
		self.commit_handler()
		await self.pull()
		if self.actions: self.act()

	async def update_status(self) -> None:
		try: await self.client.change_presence(activity=Activity(type=ActivityType.listening,name=f'last update: {nhours} hours ago' if (nhours:=int((time()-self.client.lu)/60/60)) else 'last update: just now'))
		except AttributeError: pass

	async def pull(self) -> None:
		"""pull commit from github"""
		if self.client.MODE == '/reg/nal':
			await (await create_subprocess_shell('touch updating;git reset --hard && git pull;rm updating')).wait()
		else:
			for i in range(100):
				await sleep(0.1)
				if not exists('updating'):
					await sleep(2)
					break
		await self.update_status()

	def commit_handler(self) -> None:
		for commit in self.commits:
			if msg:=commit.get('message',''):
				self.client.log.log('update',msg,False)
				if msg.startswith(('nu;','du;')): continue
			for filename in commit.get('modified'):
				match filename.split('/'):
					case [
						'main.py'|
						'client.py'|
						'utils',*_]:
						self.actions.add('reboot')
					case ['extensions',*extension]: self.actions.add(f'extensions.{extension[0].split(".")[0]}')
					case _: pass

	def act(self) -> None:
		if 'reboot' in self.actions or 'extensions._shared_vars' in self.actions:
			self.client.log.log('update',f'rebooting...',to_db=False)
			_exit(0)
		for extension in self.actions:
			if extension == 'extensions.tet' and not self.client.MODE == 'tet': continue
			self.client.reload_extension(extension)
			self.client.log.log('ext_reload',extension.split(".")[-1],to_db=False)
		self.client.git_hash()