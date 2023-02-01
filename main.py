#!./venv/bin/python3.10
from time import perf_counter,time
st = perf_counter()
from discord import Activity,ActivityType,Embed,ApplicationContext,Message,Guild,Interaction,ApplicationCommandInvokeError,SlashCommandGroup,Intents,File
from utils.tyrantlib import convert_time,format_bytes,get_line_count
from discord.ext.commands import Cog,slash_command
from traceback import format_exc,format_tb
from discord.errors import CheckFailure
from utils.pluralkit import PluralKit
from client import Client,MixedUser
from discord.ext.tasks import loop
from pymongo import MongoClient
from utils.data import db,env
from os.path import exists
from inspect import stack
from utils.log import log
from asyncio import sleep
from io import StringIO
from json import loads
from os import _exit
from sys import argv

DEV_MODE  = exists('dev')
BETA_MODE = '--beta' in argv
TET_MODE  = '--tet'  in argv

with open('.git/refs/heads/master') as git:
	git = git.read()
	with open('last_update') as file:
		last_update = file.readlines()
	if last_update[0] != git:
		lu = time()
		with open('last_update','w') as file:
			file.write(f'{git}{lu}')
	else: lu = float(last_update[1])

with open('mongo') as mongo:
	mongo = MongoClient(mongo.read())['reg-nal']['INF']
	doc = mongo.find_one({'_id':'/reg/nal'})
	extensions = doc['extensions']
	benv = doc['env']

if DEV_MODE:
	with open('dev') as dev:
		dev = loads(dev.read())
		extensions = dev['extensions']

class client_cls(Client):
	def __init__(self) -> None:
		global extensions
		super().__init__('i lika, do, da cha cha',None,intents=Intents.all(),max_messages=100000)
		self.db = db()
		self.flags = {}
		self.au:dict = None
		self.env = env(benv['env_dict'])
		if 'clear' in argv: return
		self.log = log(self.db,DEV_MODE)
		self.pk = PluralKit()
		if not BETA_MODE:
			self.add_cog(base_commands(self))
			self.add_cog(message_handler(self))
		if DEV_MODE:
			self.flags.update({'DEV':None})
			self.log.debug('LAUNCHED IN DEV MODE',to_db=False)
		with open('.git/refs/heads/master') as git: self.commit_id = git.read(7)
		self.loaded_extensions,self._raw_loaded_extensions = [],[]
		for extension,enabled in extensions.items():
			if enabled:
				self.load_extension(f'extensions.{extension}')
				self.loaded_extensions.append(extension)
		self.generate_line_count()

	def generate_line_count(self):
		unloaded_extensions = [ext for ext in extensions.keys() if ext not in self.loaded_extensions]
		self.lines = sum([
			get_line_count('main.py'),
			get_line_count('utils',['__pycache__','_testing']),
			get_line_count('extensions',['__pycache__','.old','shared']+unloaded_extensions,['_shared_vars.py']+[f'{u}.py' for u in unloaded_extensions])])

	async def _owner_init(self) -> None:
		app = await self.application_info()
		if app.team: self.owner_ids = {m.id for m in app.team.members}
		else: self.owner_id = app.owner.id

	def _extloaded(self) -> None:
		if len(ext:=stack()[1].filename.split('extensions/')[-1].split('/')) == 1:
			extension = ext[0].replace('.py','')
		else: extension = ext[0]
		if extension in self._raw_loaded_extensions: return
		self.log.info(f'[EXT_LOAD] {extension}',to_db=False)
		self._raw_loaded_extensions.append(extension)

	async def embed_color(self,ctx:ApplicationContext|Interaction) -> int:
		return int(await self.db.guilds.read(ctx.guild.id,['config','general','embed_color']) if ctx.guild else await self.db.guilds.read(0,['config','general','embed_color']),16)

	async def hide(self,ctx:ApplicationContext|Interaction) -> bool:
		if ctx.guild:
			guild = await self.db.guilds.read(ctx.guild.id)
			match guild['config']['general']['hide_commands']:
				case 'enabled': return True
				case 'whitelist' if ctx.channel.id in guild['data']['hide_commands']['whitelist']: return True
				case 'blacklist' if ctx.channel.id not in guild['data']['hide_commands']['blacklist']: return True
				case 'disabled': pass
		try:
			if isinstance(ctx,ApplicationContext): return await self.db.users.read(ctx.author.id,['config','general','hide_commands'])
			if isinstance(ctx,Interaction): return await self.db.users.read(ctx.user.id,['config','general','hide_commands'])
		except Exception: pass
		return True
		
	async def on_connect(self) -> None:
		if 'clear' in argv:
			await self.sync_commands()
			print('cleared commands')
			_exit(0)
		await self._owner_init()
		if not DEV_MODE:
			await self.db.ready()
			await self.sync_commands()
		if DEV_MODE and 'sync' in argv: await self.sync_commands()
	
	async def on_ready(self) -> None:
		self.log.info(f'{self.user.name} connected to discord in {round(perf_counter()-st,2)} seconds',to_db=False)

	async def on_application_command_completion(self,ctx:ApplicationContext) -> None:
		if ctx.command.qualified_name.startswith('test '): return
		options = {} if ctx.selected_options is None else {i['name']:i['value'] for i in ctx.selected_options}
		await self.log.command(ctx,command=ctx.command.qualified_name,options=options)

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
		if self.client.au:
			auto_response_count = len([j for k in [list(self.client.au[i].keys()) for i in list(self.client.au.keys())] for j in k])
			if ctx.guild:
				g_au = await self.client.db.guilds.read(ctx.guild.id,['data','auto_responses','custom'])
				if g_au_count:=len([j for k in [list(g_au[i].keys()) for i in list(g_au.keys())] for j in k]):
					auto_response_count = f'{auto_response_count}(+{g_au_count})'
			embed.add_field(name='auto responses',value=auto_response_count,inline=True)
		for name in ['db_reads','db_writes','messages_seen','commands_used']:
			session_stat = await self.client.db.stats.read(2,["stats",name])
			lifetime.append(f'{name}: {"{:,}".format(await self.client.db.stats.read(1,["stats",name])+session_stat)}')
			session.append(f'{name}: {"{:,}".format(session_stat)}')

		embed.add_field(name='total db size',value=format_bytes((await self.client.db.messages.raw.database.command('dbstats'))['dataSize']),inline=False)
		embed.add_field(name='session',value='\n'.join(session),inline=True)
		embed.add_field(name='lifetime',value='\n'.join(lifetime),inline=True)
		embed.set_footer(text=f'version {await self.client.db.inf.read("/reg/nal",["version"])} ({self.client.commit_id})')
		await ctx.followup.send(embed=embed,ephemeral=await self.client.hide(ctx))
	
	@slash_command(
		name='ping',
		description='get /reg/nal\'s ping to discord')
	async def slash_ping(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'pong! {round(self.client.latency*100,1)}ms',ephemeral=await self.client.hide(ctx))

	@loop(minutes=5)
	async def uptime_loop(self) -> None:
		await sleep(5)
		nhours = int((time()-lu)/60/60)
		try: await self.client.change_presence(activity=Activity(type=ActivityType.listening,name=f'last update: {nhours} hours ago' if nhours else 'last update: just now'))
		except AttributeError: pass

class message_handler(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	@Cog.listener()
	async def on_guild_join(self,guild:Guild) -> None:
		# create new guild document if current guild doesn't exist
		if not await self.client.db.guilds.read(guild.id):
			await self.client.db.guilds.new(guild.id)
			await self.client.db.guilds.write(guild.id,['name'],guild.name)
			await self.client.db.guilds.write(guild.id,['owner'],guild.owner.id)

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		await self.client.db.stats.inc(2,['stats','messages_seen'])
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
		if not (user:=await self.client.db.users.read(author.id)):
			await self.client.db.users.new(author.id)
			if author.type == 'pluralkit':
				await self.client.db.users.write(author.id,['pluralkit'],True)
				await self.client.db.users.write(author.id,['config','general','talking_stick'],False)
			else: await self.client.db.users.write(author.id,['bot'],author.bot)
			user = await self.client.db.users.read(author.id)
			
		# check user no_track
		if user.get('config',{}).get('general',{}).get('no_track',False): return
		# updates username and discriminator every 50 messages
		if user.get('messages',0)%50 == 0:
			await self.client.db.users.write(author.id,['username'],author.name)
			await self.client.db.users.write(author.id,['discriminator'],author.discriminator)
		# increase user message count
		await self.client.db.users.inc(author.id,['messages'])
		if message.guild:
			# create new guild document if current guild doesn't exist
			if not (guild:=await self.client.db.guilds.read(message.guild.id)):
				await self.on_guild_join(message.guild)
				guild = await self.client.db.guilds.read(message.guild.id)
			# increase user message count on guild leaderboard
			await self.client.db.guilds.inc(message.guild.id,['data','leaderboards','messages',str(author.id)])
			# if author not in active member or ignored, add to active member list
			if author.bot: return
			if author.id in guild.get('data',{}).get('talking_stick',{}).get('active',[]): return
			if user.get('config',{}).get('ignored',False): return
			if ts_limit:=guild.get('config',{}).get('talking_stick',{}).get('limit',None):
				if not author.get_role(ts_limit): return

			await self.client.db.guilds.append(message.guild.id,['data','talking_stick','active'],author.id)

client = client_cls()

if __name__ == '__main__':
	try: client.run(client.env.beta_token if BETA_MODE else client.env.dev_token if DEV_MODE else client.env.tet_token if TET_MODE else client.env.token)
	except SystemExit: pass
