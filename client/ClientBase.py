from discord import AutoShardedBot,Interaction,ApplicationContext,Embed,Webhook,File
from utils.db import MongoDatabase
from time import perf_counter
from utils.log import Logger
from aiofiles import open
from utils.models import Project
from utils.tyrantlib import get_last_update
from tomllib import loads
from utils.classes import AutoResponses
from discord.errors import CheckFailure,ApplicationCommandInvokeError
from traceback import format_exc,format_tb
from aiohttp import ClientSession
from io import StringIO
from .Helper import ClientHelpers

class ClientBase:
	def __init__(self,project_data:Project) -> None:
		self._st = perf_counter()
		self.project = project_data
		self.db = MongoDatabase(self.project.mongo.uri)
		self.log = Logger(self.project.parseable.base_url+self.project.bot.logstream,self.project.parseable.token)
		self.helpers = ClientHelpers(self.db)
		self.au = AutoResponses()
		self._initialized = False

	async def initialize(self) -> None:
		await self.db.connect()
		await self.log.logstream_init()
		self.last_update = await get_last_update()
		self._initialized = True
	
	async def start(self) -> None:
		if not self._initialized: await self.initialize()
		await self.login(self.project.bot.token)
		await self.connect(reconnect=True)
	
	async def _owner_init(self) -> None:
		app = await self.application_info()
		self.owner_ids = {m.id for m in app.team.members} if app.team else {app.owner.id}
		self.owner_id = list(self.owner_ids)[0] # set because Bot.owner_id is given, never used in practice
	
	async def on_connect(self) -> None:
		await self.sync_commands()
		await self._owner_init()
	
	async def on_ready(self) -> None:
		self.log.info(f'{self.user.name} connected to discord in {round(perf_counter()-self._st,2)} seconds with {self.shard_count} shard{"s" if self.shard_count != 1 else ""}',to_db=False)

	async def on_unknown_application_command(self,interaction:Interaction) -> None:
		await interaction.response.send_message('u wot m8?',ephemeral=True)
	
	async def on_application_command(self,ctx:ApplicationContext) -> None:
		ctx.output = {}
		self.log.custom('command',f'{ctx.author} used {ctx.command.name}',ctx.guild_id)
	
	async def on_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		if isinstance(error,CheckFailure): return
		await self.log.error(str(error),ctx.guild_id,traceback="".join(format_tb(error.original.__traceback__)))
	
	async def on_application_command_error(self,ctx:ApplicationContext|Interaction,error:ApplicationCommandInvokeError) -> None:
		if isinstance(error,CheckFailure): return
		embed = Embed(title='an error has occurred!',description='the issue has been automatically reported and should be fixed soon.',color=0xff6969)
		embed.add_field(name='error',value=str(error))

		if isinstance(ctx,Interaction):
			if not ctx.response.is_done(): await ctx.response.send_message(embed=embed,ephemeral=True)
			else: await ctx.followup.send(embed=embed,ephemeral=True)
		else: await ctx.respond(embed=embed,ephemeral=True)

		traceback = "".join(format_tb(error.original.__traceback__))
		self.log.error(str(error),guild_id=ctx.guild_id,traceback=traceback)

		async with ClientSession() as session:
			wh = Webhook.from_url(self.project.webhooks.errors,session=session)
			if len(traceback)+8 > 2000: await wh.send(file=File(StringIO(traceback),'error.txt'))
			else: await wh.send(f'```\n{traceback}\n```')
		
	async def on_error(self,event:str,*args,**kwargs) -> None:
		async with ClientSession() as session:
			wh = Webhook.from_url(self.project.webhooks.errors,session=session)
			error = format_exc()
			if len(error)+8 > 2000: await wh.send(file=File(StringIO(error),'error.txt'))
			else: await wh.send(f'```\n{error}\n```')