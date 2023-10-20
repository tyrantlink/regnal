from aiohttp.web import Application,AppRunner,TCPSite,HTTPForbidden
from client import ClientLarge,ClientSmall,Client
from utils.models import BotData,BotType,Project
from aiohttp.web_response import Response
from aiohttp.web_request import Request
from hmac import new,compare_digest
from config import LIVE_RELOAD
from watchfiles import awatch
from utils.log import Logger
from hashlib import sha256
from tomllib import loads
from aiofiles import open
from os import walk


class UpdateHandler:
	def __init__(self,logger:Logger,bots:dict[str,Client],base_project:dict,github_secret:str) -> None:
		self.log = logger
		self.bots = bots
		self.base_project = base_project
		self.secret = github_secret
		self._updating = False

	async def initialize(self) -> None:
		app = Application()
		app.router.add_post('/github-commit',self.handle_post)
		web_app = AppRunner(app)
		await web_app.setup()
		site = TCPSite(web_app,'0.0.0.0', 7364)  # Replace with your host and port
		await site.start()
		await self.change_monitor()

	async def handle_post(self,request:Request) -> Response:
		# check for header
		if (signature:=request.headers.get("X-Hub-Signature-256",None)) is None:
			self.log.info(f'received post request from {request.remote} without x-hub-signature-256 header')
			raise HTTPForbidden(reason='x-hub-signature-256 header is missing!')
		# verify signature
		expected = f'sha256={new(self.secret.encode("utf-8"), msg=await request.read(), digestmod=sha256).hexdigest()}'
		if not compare_digest(expected,signature):
			self.log.info(f'received post request from {request.remote} with invalid signature')
			raise HTTPForbidden(reason='signature doesn\'t match!')

		self.log.info(f'received post request from {request.remote} with valid signature')
		self._updating = True
		# await (await create_subprocess_shell('git reset --hard && git pull')).wait()
		self._updating = False
		return Response()

	async def severe_change(self,file_path:str) -> None:
		self.log.info(f'severe change detected to {file_path}; rebooting')
		exit(0)

	async def bot_start(self,bot_name:str) -> None:
		async with open(f'bots/{bot_name}/bot.toml','r') as f:
			bot_data = BotData.model_validate(loads(await f.read()))
		if not bot_data.enabled:
			self.log.info(f'skipping changes made to {bot_name} because it is disabled')
			return
		proj = self.base_project.copy()
		proj['bot'] = bot_data
		match bot_data.type:
			case BotType.LARGE: self.bots.update({bot_name:ClientLarge(Project.model_validate(proj))})
			case BotType.SMALL: self.bots.update({bot_name:ClientSmall(Project.model_validate(proj))})
			case _: raise ValueError(f'invalid bot type {bot_data.type}')
		self.log.info(f'prepared {bot_name} for launch')
		extensions = next(walk('extensions'))[1]
		for extension in extensions:
			if extension in bot_data.disabled_extensions: continue
			self.bots[dir].load_extension(f'extensions.{extension}')
		if bot_data.custom_extension:
			self.bots[dir].load_extension(f'bots.{dir}')
		await self.bots[bot_name].start()

	async def bot_restart(self,bot_name:str) -> None:
		if (bot:=self.bots.get(bot_name,None)) is None: await self.bot_start(bot_name)
		self.log.info(f'restarting {bot_name}')
		await bot.close()
		del self.bots[bot_name]
		await self.bot_start(bot_name)

	async def reload_extension(self,extension:str) -> None:
		for bot in self.bots.values():
			if extension in bot.project.bot.disabled_extensions: continue
			if extension in bot.extensions:
				bot.reload_extension(extension)
				continue
			if extension.split('.') == 'bots': continue # if it was a custom extension, it must either be disabled or was already loaded
			bot.load_extension(extension)

	async def change_monitor(self) -> None:
		if not LIVE_RELOAD: return
		self.log.info('started change monitor')
		async for changes in awatch('.'):
			actions = set()
			for change_type,file_path in list(changes):
				if change_type.name != 'modified': await self.severe_change(file_path)
				file_path = file_path.split('/./')[-1]
				match file_path.split('/'):
					case ['client'|'utils'|'main.py'|'project.toml',*additional]:
						await self.severe_change(file_path)
					case ['bots',bot_name,'bot.toml']:
						actions.add((self.bot_restart,bot_name))
					case ['bots',bot_name,*additional]:
						actions.add((self.reload_extension,f'bots.{bot_name}'))
					case ['extensions',extension_name,*additional]:
						actions.add((self.reload_extension,f'extensions.{extension_name}'))
					case _: continue
			for action,arg in actions:
				await action(arg)

 