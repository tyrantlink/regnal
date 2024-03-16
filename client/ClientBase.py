from discord import Interaction,ApplicationContext,Embed,Webhook,File,Activity,ActivityType,Guild,Message
from discord.errors import CheckFailure,ApplicationCommandInvokeError,HTTPException
if not 'TYPE_HINT': from extensions.auto_responses import AutoResponses
from utils.db import MongoDatabase,Guild as GuildDocument
from .permissions import PermissionHandler
from traceback import format_exc,format_tb
from utils.models import Project,BotType
from utils.tyrantlib import get_version
from utils.log import Logger,LogLevel
from time import perf_counter,time
from discord.ext.tasks import loop
from .commands import BaseCommands
from aiohttp import ClientSession
from .Helper import ClientHelpers
from config import DEV_MODE
from .config import Config
from io import StringIO
from .api import CrAPI


class ClientBase:
	def __init__(self,project_data:Project) -> None:
		self._st = perf_counter()
		self.project = project_data
		self.db = MongoDatabase(self.project.mongo.uri)
		self.log = Logger(
			url = self.project.parseable.base_url,
			logstream = self.project.bot.logstream,
			logstream_padding = self.project.parseable.logstream_padding,
			token = self.project.parseable.token,
			log_level = LogLevel(self.project.config.log_level))
		self.helpers = ClientHelpers(self)
		self.au:AutoResponses = None # set by auto responses extension
		self.logging_ignore:set = None # set by logging extension
		self.recently_deleted:set = set() # used by logging extension
		self.api = CrAPI(self)
		self.permissions = PermissionHandler(self)
		self.config = Config(self)
		self.last_update_hour = -1
		self._initialized = False

	async def initialize(self) -> None:
		await self.db.connect()
		await self.api.connect()
		await self.log.logstream_init()
		self.version = await get_version(
			self.project.config.git_branch,
			self.project.config.start_commit,
			self.project.config.base_version)
		self._initialized = True

	async def start(self) -> None:
		if not self._initialized: await self.initialize()
		await self.login(self.project.bot.token)
		await self.connect(reconnect=True)

	async def _owner_init(self) -> None:
		app = await self.application_info()
		self.owner_ids = {m.id for m in app.team.members} if app.team else {app.owner.id}
		self.owner_id = list(self.owner_ids)[0] # set because Bot.owner_id is given

	async def on_connect(self) -> None:
		await self.sync_commands()
		await self._owner_init()
		shards = f' with {self.shard_count} shard{"s" if self.shard_count != 1 else ""}' if self.shard_count is not None else ''
		self.log.info(f'{self.user.name} connected to discord in {round(perf_counter()-self._st,2)} seconds{shards}')
		if not self.update_presence.is_running():
			self.update_presence.start()

	async def on_ready(self) -> None:
		self.helpers.load_commands() #? i have to delay this to here because it's stupid or something
		self.log.info(f'{self.user.name} ready in {round(perf_counter()-self._st,2)} seconds')

	async def on_unknown_application_command(self,interaction:Interaction) -> None:
		await interaction.response.send_message('u wot m8?',ephemeral=True)

	async def on_application_command(self,ctx:ApplicationContext) -> None:
		self.log.info(f'{ctx.author.name} used {ctx.command.name}',ctx.guild_id)

	async def on_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		if isinstance(error,CheckFailure): return
		await self.log.error(str(error),ctx.guild_id,traceback="".join(format_tb(error.original.__traceback__)))
		if DEV_MODE: "".join(format_tb(error.original.__traceback__))

	async def on_application_command_error(self,ctx:ApplicationContext|Interaction,error:ApplicationCommandInvokeError) -> None:
		if isinstance(error,CheckFailure): return
		embed = Embed(title='an error has occurred!',description='the issue has been automatically reported and should be fixed soon.',color=0xff6969)
		embed.add_field(name='error',value=str(error))

		await ctx.respond(embed=embed,ephemeral=True)

		traceback = "".join(format_tb(error.original.__traceback__))
		if DEV_MODE: print(traceback)
		self.log.error(str(error),guild_id=ctx.guild_id,traceback=traceback)

		async with ClientSession() as session:
			wh = Webhook.from_url(self.project.webhooks.errors,session=session)
			if len(traceback)+8 > 2000: await wh.send(
				username=self.user.name,
				avatar_url=self.user.avatar.url,
				file=File(StringIO(traceback),'error.txt'))
			else:
				await wh.send(f'```\n{traceback}\n```',
					username=self.user.name,
					avatar_url=self.user.avatar.url)

	async def on_error(self,event:str,*args,**kwargs) -> None:
		async with ClientSession() as session:
			wh = Webhook.from_url(self.project.webhooks.errors,session=session)
			error = format_exc()
			if DEV_MODE: print(error)
			if len(error)+8 > 2000: await wh.send(
				username=self.user.name,
				avatar_url=self.user.avatar.url,
				file=File(StringIO(error),'error.txt'))
			else:
				await wh.send(f'```\n{error}\n```',
					username=self.user.name,
					avatar_url=self.user.avatar.url)

	def load_extension(self,name:str) -> None:
		try: super().load_extension(name)
		except Exception as e: self.log.error(str(e),traceback="".join(format_tb(e.__traceback__)))
		self.log.info(f'loaded extension {name.split(".")[-1]}')

	async def stop(self) -> None:
		await self.close()
		self.update_presence.cancel()
		await super().close()

	#? Events
	async def on_guild_join(self,guild:Guild) -> GuildDocument:
		if self.project.bot.type == BotType.SMALL and guild.id not in [*self.project.config.base_guilds,*self.project.bot.guilds]:
			try: await guild.leave()
			except HTTPException: self.log.error(f'failed to leave guild {guild.id}')
			return

		guild_doc = await self.db.guild(guild.id)
		if guild_doc is None:
			guild_doc = self.db.new.guild(
				id=guild.id,
				name=guild.name,
				owner=guild.owner_id
			)
			await guild_doc.save()
		self.log.info(f'joined guild {guild.name} ({guild.id})')
		return guild_doc

	async def on_message(self,message:Message) -> None:
		# ignore DMs
		if message.guild is None: return
		# grab guild document
		guild = await self.db.guild(message.guild.id)
		# create doc if it doesn't exist
		guild = await self.on_guild_join(message.guild) if guild is None else guild
		# keep guild name updated
		guild.name = message.guild.name
		# ignore webhooks
		if message.webhook_id is not None: return
		# grab user document
		user = await self.db.user(message.author.id)
		# create doc if it doesn't exist
		if user is None:
			user = self.db.new.user(
				id=message.author.id,
				username=message.author.name)
			await user.save()
		# return if user has no_track enabled
		if user.config.general.no_track: return
		# update username if changed
		if user.username != message.author.name:
			user.username = message.author.name
		# increment message count
		if str(message.guild.id) not in user.data.statistics.messages.keys():
			user.data.statistics.messages[str(message.guild.id)] = 0
		user.data.statistics.messages[str(message.guild.id)] += 1
		# bots aren't counted in activity stats
		if message.author.bot:
			await user.save_changes()
			return
		# increment guild activity stats
		day = str(guild.get_current_day())
		# check if day is in activity dict
		if day not in guild.data.activity.keys():
			guild.data.activity[day] = {}
			# remove oldest day if activity dict is too long
			while len(guild.data.activity.keys()) > 30:
				guild.data.activity.pop(sorted(list(guild.data.activity.keys()))[0])
		if str(message.author.id) not in guild.data.activity[day].keys():
			guild.data.activity[day][str(message.author.id)] = 0
		guild.data.activity[day][str(message.author.id)] += 1
		# save user and guild data to db
		await user.save_changes()
		await guild.save_changes()

	#? Tasks
	@loop(minutes=1)
	async def update_presence(self) -> None:
		if (new:=round((time()-self.version.timestamp)/3600)) != self.last_update_hour:
			self.last_update_hour = new
			status = f'last update: {self.last_update_hour} hours ago' if self.last_update_hour else 'last update: just now'
			await self.change_presence(activity=Activity(
				type=ActivityType.custom,name='a',state=status))
			self.log.debug(f'updated status to "{status}"')