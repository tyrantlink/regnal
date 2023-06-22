#!./venv/bin/python3.10
from time import perf_counter,time
st = perf_counter()
from discord import Activity,ActivityType,Embed,Message,Guild,Interaction,ApplicationCommandInvokeError,SlashCommandGroup,Intents,File,ApplicationContext as ApplicationContextBase
from utils.classes import MixedUser,Env,ApplicationContext,AutoResponses
from utils.tyrantlib import convert_time,format_bytes,get_line_count
from pymongo.errors import ServerSelectionTimeoutError
from discord.ext.commands import Cog,slash_command
from traceback import format_exc,format_tb
from discord.errors import CheckFailure
from utils.updater import UpdateHandler
from utils.pluralkit import PluralKit
from asyncio import sleep,create_task
from fastapi import FastAPI,Request
from discord.ext.tasks import loop
from utils.db import MongoDatabase
from uvicorn import run as urun
from utils.nsfw import nsfw
from os.path import exists
from inspect import stack
from utils.log import log
from client import Client
from io import StringIO
from json import loads
from os import _exit
from sys import argv

MODE = 'beta' if '--beta' in argv else 'dev' if exists('dev') else 'tet' if '--tet' in argv else '/reg/nal'

class client_cls(Client):
	def __init__(self,db:MongoDatabase,extensions:dict[str,bool],env:Env) -> None:
		super().__init__('i lika, do, da cha cha',None,intents=Intents.all(),max_messages=100000)
		self.db = db
		self.flags = {}
		self.env = env
		self.au:AutoResponses = AutoResponses(self.db.auto_response(0)._col)
		self.MODE = MODE
		self.git_hash()
		if 'clear' in argv: return
		self.log = log(self.db,MODE)
		self.pk = PluralKit()
		if not MODE == 'beta':
			self.add_cog(base_commands(self))
			self.add_cog(message_handler(self))
		if MODE == 'dev':
			self.flags.update({'DEV':None})
			self.log.debug('LAUNCHED IN DEV MODE',to_db=False)
		self.loaded_extensions,self._raw_loaded_extensions = [],[]
		if (
			extensions.get('nsfw_filter',True) or
			extensions.get('sauce',True)):
			self.log.info('initializing nsfw class',False)
			self.nsfw = nsfw()
			self.log.info('initialized nsfw class',False)
		for extension,enabled in extensions.items():
			if enabled:
				self.load_extension(f'extensions.{extension}')
				self.loaded_extensions.append(extension)
		if MODE == 'tet': self.load_extension(f'extensions.tet')
		self.generate_line_count(extensions)

	def generate_line_count(self,extensions:dict[str,bool]):
		unloaded_extensions = [ext for ext in extensions.keys() if ext not in self.loaded_extensions]
		self.lines = sum([
			get_line_count('main.py'),
			get_line_count('utils',['__pycache__','_testing']),
			get_line_count('extensions',['__pycache__','.old','shared']+unloaded_extensions,['_shared_vars.py']+[f'{u}.py' for u in unloaded_extensions])])

	async def _owner_init(self) -> None:
		app = await self.application_info()
		if app.team: self.owner_ids = {m.id for m in app.team.members}
		else: self.owner_ids = {app.owner.id}
		self.owner_id = list(self.owner_ids)[0]

	def _extloaded(self) -> None:
		if len(ext:=stack()[1].filename.split('extensions/')[-1].split('/')) == 1:
			extension = ext[0].replace('.py','')
		else: extension = ext[0]
		if extension in self._raw_loaded_extensions: return
		self.log.log('EXT_LOAD',extension,to_db=False)
		self._raw_loaded_extensions.append(extension)

	async def embed_color(self,ctx:ApplicationContext|Interaction) -> int:
		return int(await self.db.guild(ctx.guild.id).config.general.embed_color.read() if ctx.guild else await self.db.guild(0).config.general.embed_color.read(),16)

	async def hide(self,ctx:ApplicationContext|Interaction) -> bool:
		if ctx.guild:
			guild = await self.db.guild(ctx.guild.id).read()
			match guild['config']['general']['hide_commands']:
				case 'enabled': return True
				case 'whitelist' if ctx.channel.id in guild['data']['hide_commands']['whitelist']: return True
				case 'blacklist' if ctx.channel.id not in guild['data']['hide_commands']['blacklist']: return True
				case 'disabled': pass
		try:
			if isinstance(ctx,ApplicationContext|ApplicationContextBase): return await self.db.user(ctx.author.id).config.general.hide_commands.read()
			if isinstance(ctx,Interaction): return await self.db.user(ctx.user.id).config.general.hide_commands.read()
		except Exception: pass
		return True

	def git_hash(self) ->None:
		with open('.git/refs/heads/master') as git:
			git = git.read()
			self.commit_id = git[:7]
			with open('last_update') as file:
				last_update = file.readlines()
			if last_update[0] != git:
				self.lu = time()
				with open('last_update','w') as file:
					file.write(f'{git}{self.lu}')
			else: self.lu = float(last_update[1])

	async def on_ready(self) -> None:
		if 'clear' in argv:
			await self.sync_commands()
			print('cleared commands')
			_exit(0)
		await self._owner_init()
		if MODE in ['/reg/nal','tet']: await self.sync_commands()
		elif 'sync' in argv: await self.sync_commands()
		await self.au.reload_au()
		self.log.info(f'{self.user.name} connected to discord in {round(perf_counter()-st,2)} seconds with {self.shard_count} shard{"s" if self.shard_count != 1 else ""}',to_db=False)

	async def on_application_command(self,ctx:ApplicationContext) -> None:
		ctx.output = {}

	async def on_application_command_completion(self,ctx:ApplicationContext) -> None:
		if ctx.command.qualified_name.startswith('test '): return
		await self.log.command(ctx,command=ctx.command.qualified_name,
			input={} if ctx.selected_options is None else {i['name']:i['value'] for i in ctx.selected_options},
			output=ctx.output)

	async def on_unknown_application_command(self,interaction:Interaction) -> None:
		await interaction.response.send_message('u wot m8?',ephemeral=True)

	async def on_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		if isinstance(error,CheckFailure): return
		await self.log.error(error,ctx=ctx)

	async def on_application_command_error(self,ctx:ApplicationContext|Interaction,error:ApplicationCommandInvokeError) -> None:
		if isinstance(error,CheckFailure): return
		embed = Embed(title='an error has occurred!',description='the issue has been automatically reported and should be fixed soon.',color=0xff6969)
		embed.add_field(name='error',value=str(error))
		if isinstance(ctx,Interaction):
			if not ctx.response.is_done(): await ctx.response.send_message(embed=embed,ephemeral=True)
			else: await ctx.followup.send(embed=embed,ephemeral=True)
		else: await ctx.respond(embed=embed,ephemeral=True)
		await self.log.error(error,ctx=ctx)
		channel = self.get_channel(1026593781669167135) or await self.fetch_channel(1026593781669167135)
		err = "".join(format_tb(error.original.__traceback__))
		if len(err)+8 > 2000: await channel.send(file=File(StringIO(err),'error.txt'))
		else: await channel.send(f'```\n{err}\n```')

	async def on_error(self,event:str,*args,**kwargs) -> None:
		channel = self.get_channel(1026593781669167135) or await self.fetch_channel(1026593781669167135)
		error = format_exc()
		if len(error)+8 > 2000: await channel.send(file=File(StringIO(error),'error.txt'))
		else: await channel.send(f'```\n{error}\n```')

class base_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.uptime_loop.start()

	@slash_command(
		name='stats',
		description='get /reg/nal\'s session stats')
	async def slash_stats(self,ctx:ApplicationContext) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		age = divmod(int((time()-self.client.user.created_at.timestamp())/60/60/24),365)
		embed = Embed(
			title='/reg/nal stats:',
			description=f'{age[0]} year{"s" if age[0] != 1 else ""} and {age[1]} day{"s" if age[1] != 1 else ""} old',
			color=await self.client.embed_color(ctx))
		lifetime,session  = [],[]
		embed.add_field(name='uptime',value=convert_time(perf_counter()-st,3),inline=False)
		embed.add_field(name='guilds',value=len([guild for guild in self.client.guilds if guild.member_count >= 5]),inline=True)
		embed.add_field(name='line count',value=f'{self.client.lines} lines',inline=True)
		embed.add_field(name='commands',value=len([cmd for cmd in self.client.walk_application_commands() if not isinstance(cmd,SlashCommandGroup)]),inline=True)
		auto_response_count = str(len(self.client.au.find({'guild':None,'user':None})))
		if ctx.guild:
			if g_au:=[str(i) for i in [
				len(self.client.au.find({'custom':False,'guild':str(ctx.guild.id)})),
				len(self.client.au.find({'custom':True,'guild':str(ctx.guild.id)}))] if i]:
					auto_response_count += f'({"+" if len(g_au) == 1 else ""}{"+".join(g_au)})'
		embed.add_field(name='auto responses',value=auto_response_count,inline=True)
		lifetime_stats = await self.client.db.status_log(1).stats.read()
		for name in ['db_reads','db_writes','messages_seen','commands_used']:
			lifetime.append(f'{name}: {"{:,}".format(lifetime_stats.get(name)+self.client.db.session_stats.get(name))}')
			session.append(f'{name}: {"{:,}".format(self.client.db.session_stats.get(name))}')

		embed.add_field(name='total db size',value=format_bytes((await self.client.db.inf(0)._col.database.command('dbstats'))['dataSize']),inline=False)
		embed.add_field(name='session',value='\n'.join(session),inline=True)
		embed.add_field(name='lifetime',value='\n'.join(lifetime),inline=True)
		embed.set_footer(text=f'version {await self.client.db.inf("/reg/nal").version.read()} ({self.client.commit_id})')
		await ctx.followup.send(embed=embed,ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='ping',
		description='get /reg/nal\'s ping to discord')
	async def slash_ping(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'pong! {round(self.client.latency*100,1)}ms',ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='donate',
		description='pls donate am broke')
	async def slash_donate(self,ctx:ApplicationContext) -> None:
		embed = Embed(
			description='uhhh, this is for donations, i refuse to lock any features behind a paywall, at best you can donate so i\'ll get something done faster, but that feature will be public for everyone.\n\nif your server is big enough, i might do a unique spin off that uses the same backend as /reg/nal, but with a different name and icon, just shoot me a dm from the [development server](<https://discord.gg/4mteVXBDW7>)\n\nanywho, no need to donate, it just helps me uh, work on stuff more often, i guess.',
			color=await self.client.embed_color(ctx))
		embed.set_author(name='donation',icon_url='https://cdn.tyrant.link/blurple_tyrantlink.png')
		embed.add_field(name='github sponsors',value='https://github.com/sponsors/tyrantlink',inline=False)
		embed.add_field(name='monero (XMR)',value='`899YLWhurE1d4rMnNEbLUChXvRtQ6uiwbUCwEcy9gdSaDgJkHE5EWQPT31YKrATtcoRVUa1regt4mKLhhEhi38Kh1WjVNuz`',inline=False)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))

	@loop(minutes=5)
	async def uptime_loop(self) -> None:
		await sleep(5)
		nhours = int((time()-self.client.lu)/60/60)
		try: await self.client.change_presence(activity=Activity(type=ActivityType.listening,name=f'last update: {nhours} hours ago' if nhours else 'last update: just now'))
		except AttributeError: pass

class message_handler(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	@Cog.listener()
	async def on_guild_join(self,guild:Guild) -> None:
		# create new guild document if current guild doesn't exist
		if not await self.client.db.guild(guild.id).read():
			await self.client.db.guild(0).new(guild.id)
			await self.client.db.guild(guild.id).name.write(guild.name)
			await self.client.db.guild(guild.id).owner.write(guild.owner.id)

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		self.client.db.session_stats['messages_seen'] += 1
		# ignore webhooks
		if message.webhook_id is not None: return
		# wait for pluralkit
		author = None
		if (pk:=await self.client.pk.get_message(message.id)) is not None:
			author = MixedUser('pluralkit',pk.member,
				id=pk.member.uuid,
				name=pk.member.name,
				discriminator=None,
				bot=True)
		else: # message is not a pluralkit message
			author = MixedUser('discord',message.author,
				id=message.author.id,
				name=message.author.name,
				discriminator=message.author.discriminator,
				bot=message.author.bot)

		# create new user document if author doesn't exist
		if not (user:=await self.client.db.user(author.id).read()):
			await self.client.db.user(0).new(author.id)
			if author.type == 'pluralkit':
				await self.client.db.user(author.id).pluralkit.write(True)
				await self.client.db.user(author.id).config.general.talking_stick.write(False)
			else: await self.client.db.user(author.id).bot.write(author.bot)
			user = await self.client.db.user(author.id).read()

		# check user no_track
		if user.get('config',{}).get('general',{}).get('no_track',False): return
		# updates username and discriminator every 50 messages
		if user.get('messages',0)%50 == 0:
			await self.client.db.user(author.id).username.write(author.name)
			await self.client.db.user(author.id).discriminator.write(author.discriminator)
		# increase user message count
		await self.client.db.user(author.id).messages.inc()
		if message.guild:
			# create new guild document if current guild doesn't exist
			if not (guild:=await self.client.db.guild(message.guild.id).read()):
				await self.on_guild_join(message.guild)
				guild = await self.client.db.guild(message.guild.id).read()
			# increase user message count on guild leaderboard
			await self.client.db.guild(message.guild.id).inc(1,['data','leaderboards','messages',str(author.id)])
			# if author not an active member, dev banned, or ignored, add to active member list
			if (author.bot or
					user.get('config',{}).get('general',{}).get('ignored',False) or
					author.id in [*guild.get('data',{}).get('talking_stick',{}).get('active',[]),
					*(await self.client.db.inf('/reg/nal').banned_users.read())]): return
			if ts_limit:=guild.get('config',{}).get('talking_stick',{}).get('limit',None):
				if not author.get_role(ts_limit): return

			await self.client.db.guild(message.guild.id).data.talking_stick.active.append(author.id)

async def start():
	global client
	with open('mongo') as mongo:
		try: db = MongoDatabase(mongo.read())
		except ServerSelectionTimeoutError: _exit()
	doc = await db.inf('/reg/nal').read()
	extensions = doc['extensions']

	if MODE in ['dev','beta']:
		with open('dev') as dev:
			dev = loads(dev.read())
			extensions = dev['extensions']
	client = client_cls(db,extensions,Env(doc['env']))
	try:
		match MODE:
			case '/reg/nal': await client.start(client.env.token)
			case 'tet': await client.start(client.env.tet_token)
			case 'dev': await client.start(client.env.dev_token)
			case 'beta': await client.start(client.env.beta_token)
	finally:
		lifetime,session = await db.status_log(1).stats.read(),db.session_stats
		for i in ['db_reads','db_writes','messages_seen','commands_used']: lifetime[i] += session[i]
		await db.status_log(1).stats.write(lifetime)

api = FastAPI(docs_url=None)

@api.on_event('startup')
async def startup_event():
	create_task(start())

@api.post('/github-commit',status_code=200)
async def on_update(request:Request) -> None:
	await UpdateHandler(client,loads(await request.body())).run()

if __name__ == '__main__':
	try: urun(api,host='0.0.0.0',port=7364,log_level='critical')
	except SystemExit: pass