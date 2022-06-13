#!./venv/bin/python3.10
from time import perf_counter
st = perf_counter()
from discord import Activity,ActivityType,Embed,ApplicationContext,Message,Guild
from utils.tyrantlib import convert_time,load_data,format_bytes
from discord.ext.commands import Cog,Bot,slash_command
from requests.auth import HTTPDigestAuth
from discord.errors import CheckFailure
from discord.ext.tasks import loop
from pymongo import MongoClient
from utils.data import db,env
from datetime import datetime
from discord import Intents
from os.path import exists
from inspect import stack
from utils.log import log
from requests import get
from os import urandom
from sys import argv

DEV_MODE = exists('dev')

with open('mongo') as mongo:
	mongo = MongoClient(mongo.read())['reg-nal']['INF']
	extensions = mongo.find_one({'_id':'/reg/nal'})['extensions']
	benv = mongo.find_one({'_id':'env'})
	config = benv['config']
	activity_options = benv['activities']

class client_cls(Bot):
	def __init__(self) -> None:
		global extensions
		super().__init__('i lika, do, da cha cha',None,intents=Intents.all())
		self.MISSING = urandom(16).hex()
		self.db = db()
		self.env = env(benv['env_dict'])
		self.help = benv['help']
		self.log = log(self.db,self.env.reglog,DEV_MODE)
		self.add_cog(base_commands(self))
		self.add_cog(message_handler(self))
		self.loaded_extensions,self._raw_loaded_extensions = [],[]
		for extension in extensions:
			if extensions[extension]:
				self.load_extension(f'extensions.{extension}')
	
	def _extloaded(self) -> None:
		cog = stack()[1].filename.replace('.py','').split('/')[-1]
		if cog in self._raw_loaded_extensions: return
		
		self.loaded_extensions.append(f'[{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}]{" [DEV] " if DEV_MODE else " "}[EXT_LOAD] {cog}')
		self._raw_loaded_extensions.append(cog)

	async def embed_color(self,ctx:ApplicationContext) -> int:
		return await self.db.guilds.read(ctx.guild.id,['config','embed_color']) if ctx.guild else await self.db.guilds.read(0,['config','embed_color'])
	
	async def hide(self,ctx:ApplicationContext) -> bool:
		return await self.db.users.read(ctx.author.id,['config','hide_commands'])

	async def on_connect(self) -> None:
		await self.db.ready()
		load_data(
			await self.db.inf.read('/reg/nal',['development','testers']),
			await self.db.inf.read('/reg/nal',['development','owner']),
			await self.db.inf.read('/reg/nal',['config','bypass_permissions']))
		await self.change_presence(activity=Activity(type=ActivityType.listening,name='last update: just now'))
		await self.log.info('successfully connected to /reg/log')
		if DEV_MODE: await self.log.debug('LAUNCHED IN DEV MODE')
		await self.log.custom('\n'.join(self.loaded_extensions),short_log='loaded extensions: '+','.join(self._raw_loaded_extensions))
	
	async def on_ready(self) -> None:
		await self.log.info(f'{self.user.name} connected to discord in {round(perf_counter()-st,2)} seconds')

	async def on_application_command_completion(self,ctx:ApplicationContext) -> None:
		if ctx.command.qualified_name.startswith('test '): return
		await self.log.command(ctx)

	async def on_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		if isinstance(error,CheckFailure): return
		await self.log.error(error)

	async def on_application_command_error(self,ctx:ApplicationContext,error:Exception) -> None:
		if isinstance(error,CheckFailure): return
		await ctx.response.send_message(error,ephemeral=True)
		await self.log.error(error)

class base_commands(Cog):
	def __init__(self,client) -> None:
		self.client:Bot = client
		self.uptime_hours = 0
		self.uptime_loop.start()
	
	@slash_command(
		name='stats',
		description='get /reg/nal\'s session stats')
	async def slash_stats(self,ctx:ApplicationContext) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))

		lifetime,session,past_price,month_price  = [],[],0,0
		embed = Embed(title='/reg/nal stats:',color=await self.client.embed_color(ctx))
		embed.add_field(name='uptime',value=convert_time(perf_counter()-st,3),inline=False)
		for name in ['db_reads','db_writes','messages_seen','commands_used']:
			session_stat = await self.client.db.stats.read(2,["stats",name])
			lifetime.append(f'{name}: {await self.client.db.stats.read(1,["stats",name])+session_stat}')
			session.append(f'{name}: {session_stat}')
		
		past = get('https://cloud.mongodb.com/api/atlas/v1.0/orgs/61c190b34a1ea5693a80727d/invoices/?pretty=true',
			auth=HTTPDigestAuth('blfmwpyu','a50bc263-a3b8-4c76-95ae-19000164e509')).json()
		current = get('https://cloud.mongodb.com/api/atlas/v1.0/orgs/61c190b34a1ea5693a80727d/invoices/pending?pretty=true',
			auth=HTTPDigestAuth('blfmwpyu','a50bc263-a3b8-4c76-95ae-19000164e509')).json()
		
		for invoice in past['results']: past_price += invoice['subtotalCents']
		for item in current['lineItems']: month_price += item['totalPriceCents']

		embed.add_field(name='session',value='\n'.join(session),inline=True)
		embed.add_field(name='lifetime',value='\n'.join(lifetime),inline=True)
		embed.add_field(name='total cost',value=f"${format((past_price+month_price)/100,'.2f')} (${format(month_price/100,'.2f')} so far this month)",inline=False)
		embed.add_field(name='total db size',value=format_bytes((await self.client.db.messages.raw.database.command('dbstats'))['dataSize']))

		await ctx.followup.send(embed=embed,ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='uptime',
		description='get /reg/nal\'s uptime')
	async def slash_uptime(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(convert_time(perf_counter()-st,3),ephemeral=await self.client.hide(ctx))

	@loop(minutes=5)
	async def uptime_loop(self) -> None:
		nhours = int((perf_counter()-st)/60/60)
		if nhours == self.uptime_hours: return
		await self.client.change_presence(activity=Activity(type=ActivityType.listening,name=f'last update: {nhours} hours ago'))
		self.uptime_hours = nhours

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
			if message.author.bot: await self.client.db.users.write(message.author.id,['bot'],True)
			
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
			# if author not in active member or softbanned or ignored, add to active member list
			if message.author.bot: return
			if message.author.id in await self.client.db.guilds.read(message.guild.id,['active_members']): return
			if await self.client.db.users.read(message.author.id,['config','ignored']): return
			if message.author.id in await self.client.db.guilds.read(message.guild.id,['softbans']): return
			ts_limit = await self.client.db.guilds.read(message.guild.id,['roles','talking_stick_limit'])
			if ts_limit:
				if not message.author.get_role(ts_limit): return

			await self.client.db.guilds.append(message.guild.id,['active_members'],message.author.id)

client = client_cls()

if __name__ == '__main__':
	client.run(client.env.dev_token if DEV_MODE else client.env.token)
