from discord import Interaction,ApplicationContext,Embed,Webhook,File,Activity,ActivityType,Guild,Message
from discord.errors import CheckFailure,ApplicationCommandInvokeError,HTTPException
if not 'TYPE_HINT': from extensions.auto_responses import AutoResponses
from utils.db import MongoDatabase,Guild as GuildDocument
from utils.db.documents.ext.flags import UserFlags
from .permissions import PermissionHandler
from traceback import format_exc,format_tb
from utils.tyrantlib import get_version
from utils.log import Logger,LogLevel
from time import perf_counter,time
from discord.ext.tasks import loop
from aiohttp import ClientSession
from .Helper import ClientHelpers
from utils.models import Project
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
		self.owner_ids = {u['_id'] async for u in self.db._client.users.find(
			{'data.flags':{"$bitsAllSet":UserFlags.ADMIN}},
			projection={'_id':True})}
		self.owner_id = list(self.owner_ids)[0] if self.owner_ids else None # set because Bot.owner_id is given

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

	async def stat_user_command(self,ctx:ApplicationContext) -> None:
		user = await self.db.user(ctx.author.id,create_if_not_found=True)
		if user.config.general.no_track: return
		user.data.statistics.command_usage += 1
		await user.save_changes()
	
	async def stat_guild_command(self,ctx:ApplicationContext) -> None:
		guild_doc = await self.db.guild(ctx.guild_id)
		if guild_doc is None: return
		guild_doc.data.statistics.commands += 1
		await guild_doc.save_changes()

	async def on_application_command(self,ctx:ApplicationContext) -> None:
		self.log.info(f'{ctx.author.name} used {ctx.command.name}',ctx.guild_id)
		await self.stat_user_command(ctx)
		if ctx.guild_id:
			await self.stat_guild_command(ctx)

	async def on_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		if isinstance(error,CheckFailure): return
		await self.log.error(str(error),ctx.guild_id,traceback="".join(format_tb(error.original.__traceback__)))

	async def on_application_command_error(self,ctx:ApplicationContext|Interaction,error:ApplicationCommandInvokeError) -> None:
		if isinstance(error,CheckFailure): return
		embed = Embed(title='an error has occurred!',description='the issue has been automatically reported and should be fixed soon.',color=0xff6969)
		embed.add_field(name='error',value=str(error))

		await ctx.respond(embed=embed,ephemeral=True)

		traceback = "".join(format_tb(error.original.__traceback__))
		print(traceback)
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
			print(error)
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
		if self.project.bot.guilds and guild.id not in [*self.project.config.base_guilds,*self.project.bot.guilds]:
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

	async def on_guild_remove(self,guild:Guild) -> None:
		guild_doc = await self.db.guild(guild.id)
		if guild_doc is None: return
		guild_doc.attached_bot = None
		await guild_doc.save_changes()

	async def handle_user_message(self,message:Message) -> None:
		user = await self.db.user(message.author.id,create_if_not_found=True)
		user.username = message.author.name
		if user.config.general.no_track:
			await user.save_changes()
			return

		if str(message.guild.id) not in user.data.statistics.messages.keys():
			user.data.statistics.messages[str(message.guild.id)] = 0
		user.data.statistics.messages[str(message.guild.id)] += 1

		await user.save_changes()

	async def handle_guild_message(self,message:Message) -> None:
		guild = await self.db.guild(message.guild.id,create_if_not_found=True)

		if guild.attached_bot != self.user.id:
			if guild.attached_bot is not None:
				self.log.error(f'guild {guild.name} ({guild.id}) is attached to a different bot ({guild.attached_bot})',guild.id)
				# await message.guild.leave()
				return
			guild.attached_bot = self.user.id
		guild.name = message.guild.name
		guild.owner = message.guild.owner_id

		day = str(guild.get_current_day())
		save_changes = True

		guild.data.statistics.messages += 1
		if day not in guild.data.activity.keys():
			while len(guild.data.activity.keys()) > 30:
				guild.data.activity.pop(sorted(list(guild.data.activity.keys()))[0])
				save_changes = False
			guild.data.activity[day] = {}

		if not (await self.db.user(message.author.id)).config.general.no_track:
			if str(message.author.id) not in guild.data.activity[day].keys():
				guild.data.activity[day][str(message.author.id)] = 0
			guild.data.activity[day][str(message.author.id)] += 1

			if 'messages' not in guild.data.leaderboards.keys():
				guild.data.leaderboards['messages'] = {}

			if str(message.author.id) not in guild.data.leaderboards['messages'].keys():
				guild.data.leaderboards['messages'][str(message.author.id)] = 0
			guild.data.leaderboards['messages'][str(message.author.id)] += 1

		await (guild.save_changes() if save_changes else guild.save())

	async def on_message(self,message:Message) -> None:
		if (
			message.guild is None or
			message.author.bot or
			message.webhook_id
		):
			return
		await self.handle_user_message(message)
		await self.handle_guild_message(message)

	#? Tasks
	@loop(minutes=1)
	async def update_presence(self) -> None:
		if (new:=round((time()-self.version.timestamp)/3600)) != self.last_update_hour:
			self.last_update_hour = new
			status = f'last update: {self.last_update_hour} hours ago' if self.last_update_hour else 'last update: just now'
			await self.change_presence(activity=Activity(
				type=ActivityType.custom,name='a',state=status))
			self.log.debug(f'updated status to "{status}"')