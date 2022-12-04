from discord.commands import SlashCommandGroup,Option as option
from utils.tyrantlib import dev_only,get_line_count
from discord.ext.commands import Cog,slash_command
from discord import Embed,ApplicationContext
from main import client_cls,extensions
from .modals import dev_modal
from asyncio import sleep
from json import dumps
from os import system,walk


class dev_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	dev = SlashCommandGroup('dev','bot owner commands')

	@dev.command(
		name='commit',
		description='create a change-log announcement')
	@dev_only()
	async def slash_dev_commit(self,ctx:ApplicationContext) -> None:
		await ctx.send_modal(dev_modal(self.client,'commit'))

	async def format_type(self,ctx:ApplicationContext,value:str,default:str=None) -> str|int|bool|float|None:
		if '::' in value:
			i = value.split('::')

			if len(i) > 2:
				await ctx.response.send_message('value error',ephemeral=await self.client.hide(ctx))
				return '__failed__'

			match i[1]:
				case 'str'|'string': return str(i[0])
				case 'int'|'integer': return int(i[0])
				case 'bool'|'boolean': return bool(i[0])
				case 'float': return float(i[0])
				case 'null'|'none': return None
				case _:
					await ctx.response.send_message(f'type "{i[1]}" unsupported',ephemeral=await self.client.hide(ctx))
					return '__failed__'
		else:
			match default:
				case 'str': return str(value)
				case 'int': return int(value)
				case _: return value

	@slash_command(
		name='suggest',
		description='suggest a new feature for /reg/nal')
	async def slash_suggest(self,ctx:ApplicationContext) -> None:
		await ctx.send_modal(dev_modal(self.client,'suggestion'))
	
	@slash_command(
		name='issue',
		description='report an issue with /reg/nal')
	async def slash_issue(self,ctx:ApplicationContext) -> None:
		await ctx.send_modal(dev_modal(self.client,'issue'))
	
	@slash_command(
		name='ping',
		description='get /reg/nal\'s ping to discord')
	async def slash_ping(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'pong! {round(self.client.latency*100,1)}ms',ephemeral=await self.client.hide(ctx))

	@dev.command(
		name='test',
		description='used for testing, various uses',
		options=[
			option(str,name='exec',description='execute string',required=False,default=None)])
	@dev_only()
	async def slash_dev_test(self,ctx:ApplicationContext,_exec:str) -> None:
		if _exec: exec(_exec)
		else: raise Exception('just testing')

	@dev.command(
		name='clear_console',
		description='clear the console output')
	@dev_only()
	async def slash_dev_clear_console(self,ctx:ApplicationContext) -> None:
		system('clear')
		await ctx.response.send_message('successfully cleared console',ephemeral=await self.client.hide(ctx))
	
	@dev.command(
		name='echo',
		description='echo a message through /reg/nal',
		options=[
			option(str,name='message',description='message for /reg/nal to repeat'),
			option(int,name='delay',description='delay = x seconds',required=False,default=0)])
	@dev_only()
	async def slash_dev_echo(self,ctx:ApplicationContext,message:str,delay:int) -> None:
		if delay:
			await ctx.response.send_message('message queued...',ephemeral=True)
			await sleep(delay)
		await ctx.channel.send(message)
		if not delay: await ctx.response.send_message('successfully echoed message',ephemeral=True)

	@dev.command(
		name='reboot',
		description='hard reboot /reg/nal, \'cause why not?')
	@dev_only()
	async def slash_dev_reboot(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'successfully set {self.client.user.mention} to False',ephemeral=await self.client.hide(ctx))
		await self.client.log.command(ctx)
		exit(0)
	
	@dev.command(
		name='get_log',
		description='get log by id',
		options=[
			option(int,name='id',description='id of the log'),
			option(str,name='mode',description='embed or raw',choices=['embed','raw'])])
	@dev_only()
	async def slash_dev_get_log(self,ctx:ApplicationContext,log_id:int,mode:str) -> None:
		log = await self.client.db.logs.read(log_id)
		if log is None:
			await ctx.response.send_message(embed=Embed(title='ERROR',description=f'no log was found with the id `{log_id}`',color=0xff6969),ephemeral=await self.client.hide(ctx))
			return
		if mode == 'raw':
			msg = dumps(log,indent=2)
			if len(msg)+8 > 2000: await ctx.response.send_message(f'character limited\n```\n{msg[:1974]}\n```',ephemeral=await self.client.hide(ctx))
			else: await ctx.response.send_message(f'```\n{msg}\n```',ephemeral=await self.client.hide(ctx))
			return
		embed = Embed(title=f'log #{log_id}',description=log.get('log',None),color=await self.client.embed_color(ctx))
		if user:=self.client.get_user(log.get('author')): embed.set_author(name=user,icon_url=user.avatar.url)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))

	@dev.command(
		name='db',
		description='interact with mongodb',
		options=[
			option(str,name='collection',description='collection to modify',choices=['guilds','users','INF','test']),
			option(str,name='mode',description='method',choices=['read','write','append','remove','pop','increment','decrement','delete','new']),
			option(str,name='id',description='document id. use :: to specify type (int default)'),
			option(str,name='path',description='path to variable, separate by >',required=False,default=[]),
			option(str,name='value',description='value. use :: to specify type (str default)',required=False,default=None)])
	@dev_only()
	async def slash_dev_db(self,ctx:ApplicationContext,collection:str,mode:str,id:str,path:str,value:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))

		match collection:
			case 'guilds': collection = self.client.db.guilds
			case 'users': collection = self.client.db.users
			case 'INF': collection = self.client.db.inf
			case 'test': collection = self.client.db.test

		if path != []: path = path.split('>')

		id = await self.format_type(ctx,id,'int')
		if value != None: value = await self.format_type(ctx,value,'str')

		if '__failed__' in [id,value]: return

		match mode:
			case 'read': res = f'```json\n{dumps(await collection.read(id,path),indent=2)}\n```'
			case 'write': res = await collection.write(id,path,value)
			case 'append': res = await collection.append(id,path,value)
			case 'remove': res = await collection.remove(id,path,value)
			case 'pop': res = await collection.pop(id,path,value)
			case 'increment': res = await collection.inc(id,path,value if value != None else 1)
			case 'decrement': res = await collection.dec(id,path,value if value != None else 1)
			case 'delete': res = await collection.delete(id)
			case 'new': res = await collection.new(id)
			case _: res = 'the fuck did you do this shouldn\'t be possible my homefam?'

		if isinstance(res,str):
			if len(res) > 2000:
				if mode == 'read': res = res[8:-4]
				for message in [res[i:i+1988] for i in range(0,len(res),1988)]:
					await ctx.response.send_message(f'```json\n{message}\n```' if mode == 'read' else message,ephemeral=await self.client.hide(ctx))
			else:
				await ctx.response.send_message(res,ephemeral=await self.client.hide(ctx))
		elif isinstance(res,bool):
			await ctx.response.send_message(f'successfully set {">".join(path)} to {value}',ephemeral=await self.client.hide(ctx))
		else:
			await ctx.response.send_message('uhhhhhhhhh, somethin\' happened. you might wanna check it out.',ephemeral=await self.client.hide(ctx))

	@dev.command(
		name='reload',
		description='reload an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys()),
			option(bool,name='sync',description='resync commands',default=True)])
	@dev_only()
	async def slash_dev_reload(self,ctx:ApplicationContext,extension:str,sync:bool=True) -> None:
		if extension not in self.client._raw_loaded_extensions:
			await ctx.response.send_message(f'{extension} is not loaded',ephemeral=True)
			return
		self.client.reload_extension(f'extensions.{extension}')
		if sync: await self.client.sync_commands(force=True)
		self.client.lines.update({extension:sum([get_line_count(f'extensions/{extension}/{i}') for i in [f for p,d,f in walk(f'extensions/{extension}')][0]])})
		await ctx.response.send_message(f'successfully reloaded {extension}',ephemeral=True)

	@dev.command(
		name='load',
		description='load an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys()),
			option(bool,name='sync',description='resync commands',default=True)])
	@dev_only()
	async def slash_dev_load(self,ctx:ApplicationContext,extension:str,sync:bool=True) -> None:
		if extension in self.client._raw_loaded_extensions:
			await ctx.response.send_message(f'{extension} is already loaded',ephemeral=True)
			return
		self.client.load_extension(f'extensions.{extension}')
		if sync: await self.client.sync_commands()
		self.client._raw_loaded_extensions.append(extension)
		self.client.lines.update({extension:sum([get_line_count(f'extensions/{extension}/{i}') for i in [f for p,d,f in walk(f'extensions/{extension}')][0]])})
		await ctx.response.send_message(f'successfully loaded {extension}',ephemeral=True)

	@dev.command(
		name='unload',
		description='unload an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys()),
			option(bool,name='sync',description='resync commands',default=True)])
	@dev_only()
	async def slash_dev_unload(self,ctx:ApplicationContext,extension:str,sync:bool=True) -> None:
		if extension not in self.client._raw_loaded_extensions:
			await ctx.response.send_message(f'{extension} is not loaded',ephemeral=True)
			return
		self.client.unload_extension(f'extensions.{extension}')
		if sync: await self.client.sync_commands()
		response = f'successfully unloaded {extension}'
		self.client._raw_loaded_extensions.remove(extension)
		del self.client.lines[extension]
		if extension == 'dev_tools': response += '\nWARNING: THE DEV_TOOLS EXTENSION WAS UNLOADED. YOU MUST REBOOT TO USE ANYMORE DEV COMMANDS'
		await ctx.response.send_message(response,ephemeral=True)

	@dev.command(
		name='enable',
		description='enable an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys())])
	@dev_only()
	async def slash_dev_enable(self,ctx:ApplicationContext,extension:str) -> None:
		await self.client.db.inf.write('/reg/nal',['extensions',extension],True)
		await ctx.response.send_message(f'successfully enabled the {extension} extension. it will start next reboot',ephemeral=True)
	
	@dev.command(
		name='disable',
		description='disable an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys())])
	@dev_only()
	async def slash_dev_disable(self,ctx:ApplicationContext,extension:str) -> None:
		await self.client.db.inf.write('/reg/nal',['extensions',extension],False)
		response = f'successfully disabled the {extension} extension. it will not start next reboot'
		if extension == 'dev_tools': response += '\nWARNING: DEV_TOOLS WAS DISABLED. IF YOU WANT TO RE-ENABLE IT AFTER A REBOOT, YOU MUST MANUALLY ENABLE IT'
		await ctx.response.send_message(response,ephemeral=True)
	
	@dev.command(
		name='sync_commands',
		description='sync commands with the discord')
	@dev_only()
	async def slash_dev_sync_commands(self,ctx:ApplicationContext) -> None:
		await self.client.sync_commands()
		await ctx.response.send_message('successfully synced commands',ephemeral=True)