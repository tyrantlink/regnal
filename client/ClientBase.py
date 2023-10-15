from discord import Interaction,ApplicationContext,Embed,Webhook,File,Activity,ActivityType,Guild,Message
from utils.db import MongoDatabase,Guild as GuildDocument
from time import perf_counter,time
from utils.log import Logger
from utils.models import Project,BotType
from utils.tyrantlib import get_last_update
from utils.classes import AutoResponses
from discord.errors import CheckFailure,ApplicationCommandInvokeError,HTTPException
from traceback import format_exc,format_tb
from aiohttp import ClientSession
from io import StringIO
from .Helper import ClientHelpers
from discord.ext.tasks import loop
from datetime import datetime


class ClientBase:
	def __init__(self,project_data:Project) -> None:
		self._st = perf_counter()
		self.project = project_data
		self.db = MongoDatabase(self.project.mongo.uri)
		self.log = Logger(self.project.parseable.base_url+self.project.bot.logstream,self.project.parseable.token)
		self.helpers = ClientHelpers(self.db)
		self.au = AutoResponses()
		self.uptime = -1
		self._initialized = False

	async def initialize(self) -> None:
		await self.db.connect()
		await self.log.logstream_init()
		self.last_update = await get_last_update(self.project.config.git_branch)
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
		shards = f' with {self.shard_count} shard{"s" if self.shard_count != 1 else ""}' if self.shard_count is not None else ''
		self.log.info(f'{self.user.name} connected to discord in {round(perf_counter()-self._st,2)} seconds{shards}')
		self.update_presence.start()
	
	async def on_ready(self) -> None:
		self.log.info(f'{self.user.name} ready in {round(perf_counter()-self._st,2)} seconds')

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
	
	#! Events
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

	async def on_message(self,message:Message) -> None:
		# ignore DMs
		if message.guild is None: return
		# grab guild document
		guild = await self.db.guild(message.guild.id)
		# create doc if it doesn't exist
		guild = await self.on_guild_join(message.guild) if guild is None else guild
		# ignore webhooks
		if message.webhook_id is not None: return
		# grab user document
		user = await self.db.user(message.author.id)
		# create doc if it doesn't exist
		if user is None:
			user = self.db.new.user(
				id=message.author.id,
				username=message.author.name)
		# return if user has no_track enabled
		if user.config.general.no_track: return
		# update username if changed
		if user.username != message.author.name:
			user.username = message.author.name
		# increment message count
		if str(message.guild.id) not in user.data.statistics.messages.keys():
			user.data.statistics.messages[str(message.guild.id)] = 0
		user.data.statistics.messages[str(message.guild.id)] += 1
		# increment guild activity stats
		day = str(datetime.utcnow().timetuple().tm_yday)
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
		await user.save()
		await guild.save()

	#! Tasks
	@loop(minutes=1)
	async def update_presence(self) -> None:
		self.log.debug('updating presence')
		if new:=round((time()-self.last_update.timestamp)/3600) != self.uptime:
			self.uptime = new
			await self.change_presence(activity=Activity(
				type=ActivityType.custom,name='a',state=f'last update: {self.uptime} hours ago' if self.uptime else 'last update: just now'))