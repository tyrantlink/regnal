from asyncio import create_subprocess_shell
from client import Client
from os import _exit

class UpdateHandler:
	def __init__(self,client:Client,payload:dict) -> None:
		self.client = client
		self.payload = payload
		self.commits:list[dict] = payload.get('commits',[])
		self.modified = list(set([f for c in self.commits for f in c.get('modified')]))
		if self.modified == []: return
		self.actions:list[str] = []

	async def run(self) -> None:
		self.modified_handler()
		await self.pull()
		if self.actions: self.act()

	async def pull(self) -> None:
		"""pull commit from github"""
		for process in [
			create_subprocess_shell('git reset --hard',stdout=-3,stderr=-3),
			create_subprocess_shell('git pull')]:
			p = await process
			await p.communicate()

	def modified_handler(self) -> None:
		for filename in self.modified:
			match filename.split('/'):
				case [
					'main.py'|
					'client.py'|
					'utils',*_]:
					self.log.info(f'update detected, reboot required',to_db=False)
					self.actions.insert(0,'reboot')
				case ['extensions',*extension]: self.actions.append(f'extensions.{extension[0].split(".")[0]}')
				case _: pass

	def act(self) -> None:
		if 'reboot' in self.actions or 'extensions._shared_vars' in self.actions:
			self.log.info(f'rebooting...',to_db=False)
			_exit(0)
		for extension in self.actions:
			if extension == 'extensions.tet' and not self.client.MODE == 'tet': continue
			self.client.reload_extension(extension)
			self.log.info(f'[EXT_RELOAD] {extension.split(".")[-1]}',to_db=False)