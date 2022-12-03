#!./venv/bin/python3.10
from time import perf_counter,time
st = perf_counter()
from discord import Activity,ActivityType,Embed,ApplicationContext,Message,Guild,Interaction,ApplicationCommandInvokeError,SlashCommandGroup
from utils.tyrantlib import convert_time,load_data,format_bytes,get_line_count
from discord.ext.commands import Cog,Bot,slash_command
from traceback import format_exc,format_tb
from discord.errors import CheckFailure
from discord.ext.tasks import loop
from pymongo import MongoClient
from utils.data import db,env
from datetime import datetime
from discord import Intents
from os.path import exists
from inspect import stack
from utils.log import log
from asyncio import sleep
from os import _exit,walk
from json import loads
from sys import argv

DEV_MODE = exists('dev')

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
	extensions = mongo.find_one({'_id':'/reg/nal'})['extensions']
	benv = mongo.find_one({'_id':'env'})
	activity_options = benv['activities']

if DEV_MODE:
	with open('dev') as dev:
		dev = loads(dev.read())
		extensions = dev['extensions']

class client_cls(Bot):
	def __init__(self) -> None:
		global extensions
		super().__init__('i lika, do, da cha cha',None,intents=Intents.all())
		self.db = db()
		self.au:dict = None
		self.env = env(benv['env_dict'])
		if 'clear' in argv: return
		self.help = benv['help']
		self.log = log(self.db,DEV_MODE)
		self.add_cog(base_commands(self))
		self.add_cog(message_handler(self))
		self.lines = {k.split('/')[-1]:get_line_count(f'{k}.py') for k in ['main']+[f"utils/{'.'.join(i.split('.')[:-1])}" for i in [f for p,d,f in walk('utils')][0] if not (i.startswith('_') or i.endswith('.old'))]}
		with open('.git/refs/heads/master') as git: self.commit_id = git.read(7)
		self.loaded_extensions,self._raw_loaded_extensions = [],[]
		for extension in extensions:
			if extensions[extension]:
				self.load_extension(f'extensions.{extension}')
				self.lines.update({extension:sum([get_line_count(f'extensions/{extension}/{i}') for i in [f for p,d,f in walk(f'extensions/{extension}')][0]])})

	def _extloaded(self) -> None:
		cog = stack()[1].filename.split('/')[-2]
		if cog in self._raw_loaded_extensions: return

		self.loaded_extensions.append(f'[{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}]{" [DEV] " if DEV_MODE else " "}[EXT_LOAD] {cog}')
		self._raw_loaded_extensions.append(cog)

	async def embed_color(self,ctx:ApplicationContext|Interaction) -> int:
		return await self.db.guilds.read(ctx.guild.id,['config','embed_color']) if ctx.guild else await self.db.guilds.read(0,['config','embed_color'])

	async def hide(self,ctx:ApplicationContext|Interaction) -> bool:
		if ctx.guild:
			guild = await self.db.guilds.read(ctx.guild.id)
			match guild['config']['hide_commands']:
				case 'enabled': return True
				case 'whitelist' if ctx.channel.id in guild['hc']['whitelist']: return True
				case 'blacklist' if ctx.channel.id not in guild['hc']['blacklist']: return True
				case 'disabled': pass
		try:
			if isinstance(ctx,ApplicationContext): return await self.db.users.read(ctx.author.id,['config','hide_commands'])
			if isinstance(ctx,Interaction): return await self.db.users.read(ctx.user.id,['config','hide_commands'])
		except Exception: pass
		return True
		

	async def on_connect(self) -> None:
		if 'clear' in argv:
			await self.sync_commands()
			print('cleared commands')
			_exit(0)
		if not DEV_MODE:
			await self.db.ready()
			await self.sync_commands()
		load_data(
			await self.db.inf.read('/reg/nal',['development','testers']),
			await self.db.inf.read('/reg/nal',['development','owner']),
			await self.db.inf.read('/reg/nal',['config','bypass_permissions']))
		if DEV_MODE:
			await self.log.debug('LAUNCHED IN DEV MODE')
			if 'sync' in argv: await self.sync_commands()
		await self.log.info('\n'.join(self.loaded_extensions),format_print=False)
	
	async def on_ready(self) -> None:
		await self.log.info(f'{self.user.name} connected to discord in {round(perf_counter()-st,2)} seconds')

	async def on_application_command_completion(self,ctx:ApplicationContext) -> None:
		if ctx.command.qualified_name.startswith('test '): return
		options = {} if ctx.selected_options is None else {i['name']:i['value'] for i in ctx.selected_options}
		await self.log.command(ctx,command=ctx.command.qualified_name,options=options)

	async def on_unknown_application_command(self,interaction:Interaction) -> None:
		await interaction.response.send_message('u wot m8?',ephemeral=True)

	async def on_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		if isinstance(error,CheckFailure): return
		await self.log.error(error)

	async def on_application_command_error(self,ctx:ApplicationContext,error:ApplicationCommandInvokeError) -> None:
		if isinstance(error,CheckFailure): return
		embed = Embed(title='an error has occurred!',description='the issue has been automatically reported and should be fixed soon.',color=0xff6969)
		embed.add_field(name='error',value=str(error))
		await ctx.respond(embed=embed,ephemeral=True)
		await self.log.error(error)
		if (channel:=self.get_channel(1026593781669167135)) is None: channel = await self.fetch_channel(1026593781669167135)
		await channel.send(f'```\n{"".join(format_tb(error.original.__traceback__))[:1992]}\n```')
	
	async def on_error(self,event:str,*args,**kwargs) -> None:
		if (channel:=self.get_channel(1026593781669167135)) is None: channel = await self.fetch_channel(1026593781669167135)
		await channel.send(f'```\n{format_exc()[:1992]}\n```')

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
		embed.add_field(name='line count',value=f'{sum(self.client.lines.values())} lines',inline=True)
		embed.add_field(name='commands',value=len([cmd for cmd in self.client.walk_application_commands() if not isinstance(cmd,SlashCommandGroup)]),inline=True)
		if self.client.au:
			auto_response_count = len([j for k in [list(self.client.au[i].keys()) for i in list(self.client.au.keys())] for j in k])
			if ctx.guild:
				g_au = await self.client.db.guilds.read(ctx.guild.id,['au','custom'])
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

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		await self.client.db.stats.inc(2,['stats','messages_seen'])
		# create new user document if author doesn't exist
		current_data = await self.client.db.users.read(message.author.id)
		if not current_data:
			await self.client.db.users.new(message.author.id)
			await self.client.db.users.write(message.author.id,['bot'],message.author.bot)
			
		# check user no_track
		if await self.client.db.users.read(message.author.id,['config','no_track']): return
		# updates username and discriminator every 50 messages
		if await self.client.db.users.read(message.author.id,['messages'])%50 == 0:
			await self.client.db.users.write(message.author.id,['username'],message.author.name)
			await self.client.db.users.write(message.author.id,['discriminator'],message.author.discriminator)
		# increase user message count
		await self.client.db.users.inc(message.author.id,['messages'])
		if message.guild:
			# create new guild document if current guild doesn't exist
			if not await self.client.db.guilds.read(message.guild.id):
				await self.client.db.guilds.new(message.guild.id)
				await self.client.db.guilds.write(message.guild.id,['name'],message.guild.name)
			# increase user message count on guild leaderboard
			await self.client.db.guilds.inc(message.guild.id,['leaderboards','messages',str(message.author.id)])
			# if author not in active member or ignored, add to active member list
			if message.author.bot: return
			if message.author.id in await self.client.db.guilds.read(message.guild.id,['active_members']): return
			if await self.client.db.users.read(message.author.id,['config','ignored']): return
			if ts_limit:=await self.client.db.guilds.read(message.guild.id,['roles','talking_stick_limit']):
				if not message.author.get_role(ts_limit): return

			await self.client.db.guilds.append(message.guild.id,['active_members'],message.author.id)

client = client_cls()

if __name__ == '__main__':
	try: client.run(client.env.dev_token if DEV_MODE else client.env.token)
	except SystemExit: pass
