from subprocess import run
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
		self.modified_handler()
		if self.actions == []: return
		self.pull()
		self.act()

	def pull(self) -> None:
		"""pull commit from github"""
		run(['git','reset','--hard','&&','git','pull'],stdout=-3,stderr=-3)

	def modified_handler(self) -> None:
		for filename in self.modified:
			match filename.split('/'):
				case [
					'main.py'|
					'client.py'|
					'utils'
					]: self.actions.insert(0,'reboot')
				case ['extensions',*extension]: self.actions.append(f'extensions.{extension[0].split(".")[0]}')
				case _: pass

	def act(self) -> None:
		if 'reboot' in self.actions: _exit(0)
		for extension in self.actions:
			if extension == 'extensions.tet' and not self.client.MODE == 'tet': continue
			self.client.reload_extension(extension)