from discord import Embed,InputTextStyle,Interaction,User,ApplicationContext
from discord.commands import SlashCommandGroup,Option as option
from discord.ext.commands import Cog,slash_command
from utils.tyrantlib import perm,load_data
from main import client_cls,extensions
from discord.ui import InputText,Modal
from asyncio import sleep
from json import dumps
from os import system

class input_modal(Modal):
	def __init__(self,client:client_cls,format:str) -> None:
		self.client = client
		self.format = format
		match format:
			case 'commit':
				super().__init__(title='make a commit')
				self.add_item(InputText(label='title',max_length=256,style=InputTextStyle.short))
				self.add_item(InputText(label='version_bump',max_length=5,placeholder='none,patch,minor,major',style=InputTextStyle.short))
				self.add_item(InputText(label='new_features',max_length=1024,required=False,style=InputTextStyle.long))
				self.add_item(InputText(label='fixes',max_length=1024,required=False,style=InputTextStyle.long))
				self.add_item(InputText(label='notes',max_length=1024,required=False,style=InputTextStyle.long))
			case 'issue':
				super().__init__(title='submit an issue')
				self.add_item(InputText(label='title',max_length=256,placeholder='title of issue',style=InputTextStyle.short))
				self.add_item(InputText(label='details',max_length=1024,placeholder='details of issues',style=InputTextStyle.long))
			case 'suggestion':
				super().__init__(title='submit a suggestion')
				self.add_item(InputText(label='title',max_length=256,placeholder='title of suggestion',style=InputTextStyle.short))
				self.add_item(InputText(label='details',max_length=1024,placeholder='details of suggestion',style=InputTextStyle.long))
			case _: print('unknown modal format')

	def bump_version(self,current_version:str,bump_type:str) -> str:
		ma,mi,p = current_version.split('.')
		match bump_type:
			case 'major': ma,mi,p = str(int(ma)+1),'0','0'
			case 'minor': mi,p = str(int(mi)+1),'0'
			case 'patch': p = str(int(p)+1)
		return '.'.join([ma,mi,p])

	async def report(self,interaction:Interaction,type:str,title:str,details:str,author:User) -> None:
		await self.client.db.inf.inc('/reg/nal',[f'{type}_count'])
		count = await self.client.db.inf.read('/reg/nal',[f'{type}_count'])
		channel = await self.client.fetch_channel(await self.client.db.inf.read('/reg/nal',['development',f'{type}s']))
		embed = Embed(
			title=f'#{count} | {title}',
			description=author.mention,
			color=await self.client.embed_color(interaction))
		embed.add_field(name=type,value=details)
		message = await channel.send(embed=embed)
		for reaction in ['<:upvote:854594180339990528>','<:downvote:854594202439909376>']: await message.add_reaction(reaction)
		await self.client.db.inf.append('/reg/nal',[f'{type}s'],message.id)

	async def commit(self,interaction:Interaction,title:str,version_bump:str,new_features:str,fixes:str,notes:str) -> None:
		channel = await self.client.fetch_channel(await self.client.db.inf.read('/reg/nal',['development','change-log']))
		if version_bump != 'none':
			await self.client.db.inf.write('/reg/nal',['version'],self.bump_version(await self.client.db.inf.read('/reg/nal',['version']),version_bump))
		embed=Embed(title=f"v{await self.client.db.inf.read('/reg/nal',['version'])} | {title}",color=await self.client.embed_color(interaction))

		if new_features: embed.add_field(name='new features:',value=new_features,inline=False)
		if fixes: embed.add_field(name='bug fixes:',value=fixes,inline=False)
		if notes: embed.add_field(name='notes:',value=notes,inline=False)
		embed.add_field(
			name="please report bugs with /issue\ncommands may take up to an hour to update globally.",
			value='[development server](<https://discord.gg/4mteVXBDW7>)')
		embed.set_footer(text=f'version {await self.client.db.inf.read("/reg/nal",["version"])} ({self.client.commit_id})')
		message = await channel.send(embed=embed)
		await message.publish()

	async def callback(self,interaction:Interaction) -> None:
		match self.format:
			case 'commit': 
				await self.commit(interaction,self.children[0].value,self.children[1].value,self.children[2].value,self.children[3].value,self.children[4].value)
				await interaction.response.send_message('successfully announced commit',ephemeral=True)
			case 'issue': 
				await self.report(interaction,'issue',self.children[0].value,self.children[1].value,interaction.user)
				await interaction.response.send_message('thank you for reporting this issue',ephemeral=True)
			case 'suggestion': 
				await self.report(interaction,'suggestion',self.children[0].value,self.children[1].value,interaction.user)
				await interaction.response.send_message('thank you for your suggestion',ephemeral=True)
			case _: print('unknown modal format')

class dev_tools_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	dev = SlashCommandGroup('dev','bot owner commands')

	@dev.command(
		name='commit',
		description='create a change-log announcement')
	@perm('bot_owner')
	async def slash_dev_commit(self,ctx:ApplicationContext) -> None:
		await ctx.send_modal(input_modal(self.client,'commit'))

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
		await ctx.send_modal(input_modal(self.client,'suggestion'))
	
	@slash_command(
		name='issue',
		description='report an issue with /reg/nal')
	async def slash_issue(self,ctx:ApplicationContext) -> None:
		await ctx.send_modal(input_modal(self.client,'issue'))
	
	@slash_command(
		name='ping',
		description='get /reg/nal\'s ping to discord')
	async def slash_ping(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'pong! {round(self.client.latency*100,1)}ms',ephemeral=await self.client.hide(ctx))
	
	@dev.command(
		name='test',
		description='used for testing, various uses',
		options=[
			option(str,name='arg1',description='argument one',required=False,default=None),
			option(str,name='arg2',description='argument two',required=False,default=None),
			option(str,name='arg3',description='argument three',required=False,default=None),
			option(str,name='arg4',description='argument four',required=False,default=None),
			option(str,name='arg5',description='argument five',required=False,default=None,choices=['a','b','c',])])
	@perm('bot_owner')
	async def slash_dev_test(self,ctx:ApplicationContext,arg1:str,arg2:str,arg3:str,arg4:str,arg5:str) -> None:
		self.client.reload_extension('extensions.dev_tools')
		await ctx.response.send_message('cum',ephemeral=True)
	
	@dev.command(
		name='clear_console',
		description='clear the console output')
	@perm('bot_owner')
	async def slash_dev_clear_console(self,ctx:ApplicationContext) -> None:
		system('clear')
		await ctx.response.send_message('successfully cleared console',ephemeral=await self.client.hide(ctx))
	
	@dev.command(
		name='echo',
		description='echo a message through /reg/nal',
		options=[
			option(str,name='message',description='message for /reg/nal to repeat'),
			option(int,name='delay',description='delay = x seconds',required=False,default=0)])
	@perm('bot_owner')
	async def slash_dev_echo(self,ctx:ApplicationContext,message:str,delay:int) -> None:
		if delay:
			await ctx.response.send_message('message queued...',ephemeral=True)
			await sleep(delay)
		await ctx.channel.send(message)
		if not delay: await ctx.response.send_message('successfully echoed message',ephemeral=True)

	@dev.command(
		name='reboot',
		description='hard reboot /reg/nal, \'cause why not?')
	@perm('bot_owner')
	async def slash_dev_reboot(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'successfully set {self.client.user.mention} to False',ephemeral=await self.client.hide(ctx))
		await self.client.log.command(ctx)
		exit()

	@dev.command(
		name='db',
		description='interact with mongodb',
		options=[
			option(str,name='collection',description='collection to modify',choices=['guilds','users','INF','test']),
			option(str,name='mode',description='method',choices=['read','write','append','remove','pop','increment','decrement','delete','new']),
			option(str,name='id',description='document id. use :: to specify type (int default)'),
			option(str,name='path',description='path to variable, separate by >',required=False,default=[]),
			option(str,name='value',description='value. use :: to specify type (str default)',required=False,default=None)])
	@perm('tester')
	async def slash_dev_db(self,ctx:ApplicationContext,collection:str,mode:str,id:str,path:str,value:str) -> None:
		if not await perm('bot_owner',ctx):
			if mode != 'read':
				await ctx.response.send_message('testers have read-only access to db.',ephemeral=await self.client.hide(ctx))
				return
			if collection == 'INF':
				await ctx.response.send_message('testers do not have access to collection INF',ephemeral=await self.client.hide(ctx))
				return

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
		name='tester',
		description='modify verified testers',
		options=[
			option(str,name='mode',description='add // remove',choices=['add','remove']),
			option(str,name='user_id',description='id of target user')])
	@perm('bot_owner')
	async def slash_dev_tester(self,ctx:ApplicationContext,mode:str,user_id:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		match mode:
			case 'add':
				await self.client.db.inf.append('/reg/nal',['development','testers'],int(user_id))
				await ctx.response.send_message(f'successfully added {user_id} to tester list',ephemeral=await self.client.hide(ctx))
			case 'remove':
				await self.client.db.inf.remove('/reg/nal',['development','testers'],int(user_id))
				await ctx.response.send_message(f'successfully removed {user_id} from tester list',ephemeral=await self.client.hide(ctx))
		load_data(await self.client.db.inf.read('/reg/nal',['development','testers']))

	@dev.command(
		name='reload',
		description='reload an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys())])
	@perm('bot_owner')
	async def slash_dev_reload(self,ctx:ApplicationContext,extension:str) -> None:
		if extension not in self.client.loaded_extensions:
			await ctx.response.send_message(f'{extension} is not loaded',ephemeral=True)
			return
		self.client.reload_extension(f'extensions.{extension}')
		await ctx.response.send_message(f'successfully reloaded {extension}',ephemeral=True)

	@dev.command(
		name='load',
		description='load an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys())])
	@perm('bot_owner')
	async def slash_dev_load(self,ctx:ApplicationContext,extension:str) -> None:
		if extension in self.client.loaded_extensions:
			await ctx.response.send_message(f'{extension} is already loaded',ephemeral=True)
			return
		self.client.load_extension(f'extensions.{extension}')
		await ctx.response.send_message(f'successfully loaded {extension}',ephemeral=True)

	@dev.command(
		name='unload',
		description='unload an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys())])
	@perm('bot_owner')
	async def slash_dev_unload(self,ctx:ApplicationContext,extension:str) -> None:
		if extension not in self.client.loaded_extensions:
			await ctx.response.send_message(f'{extension} is not loaded',ephemeral=True)
			return
		self.client.unload_extension(f'extensions.{extension}')
		response = f'successfully unloaded {extension}'
		if extension == 'dev_tools': response += '\nWARNING: THE DEV_TOOLS EXTENSION WAS UNLOADED. YOU MUST REBOOT TO USE ANY MORE DEV COMMANDS'
		await ctx.response.send_message(response,ephemeral=True)

	@dev.command(
		name='enable',
		description='enable an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys())])
	@perm('bot_owner')
	async def slash_dev_enable(self,ctx:ApplicationContext,extension:str) -> None:
		await self.client.db.inf.write('/reg/nal',['extensions',extension],True)
		await ctx.response.send_message(f'successfully enabled the {extension} extension. it will start next reboot',ephemeral=True)
	
	@dev.command(
		name='disable',
		description='disable an extension',
		options=[
			option(str,name='extension',description='name of extension',choices=extensions.keys())])
	@perm('bot_owner')
	async def slash_dev_disable(self,ctx:ApplicationContext,extension:str) -> None:
		await self.client.db.inf.write('/reg/nal',['extensions',extension],False)
		response = f'successfully disabled the {extension} extension. it will not start next reboot'
		if extension == 'dev_tools': response += '\nWARNING: DEV_TOOLS WAS DISABLED. IF YOU WANT TO RE-ENABLE IT AFTER A REBOOT, YOU MUST MANUALLY ENABLE IT'
		await ctx.response.send_message(response,ephemeral=True)
	
	@dev.command(
		name='sync_commands',
		description='sync commands with the discord')
	@perm('bot_owner')
	async def slash_dev_sync_commands(self,ctx:ApplicationContext) -> None:
		await self.client.sync_commands()
		await ctx.response.send_message('successfully synced commands',ephemeral=True)

def setup(client:client_cls) -> None: client.add_cog(dev_tools_cog(client))
