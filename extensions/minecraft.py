from discord.commands import SlashCommandGroup,Option as option
from discord import ApplicationContext
from discord.ext.commands import Cog
from utils.tyrantlib import has_perm
from websockets import connect
from json import loads,dumps
from asyncio import wait_for
from main import client_cls
from discord import Embed

class packets:
	base = lambda self,type,server,user: {'protocal': 1,'type':type,'data':{'server':server,'user':{'id':user.id,'username':user.server,'discriminator':user.discriminator}}}
	add = lambda self,server,user: self.base('add',server,user)
	update = lambda self,server,user: self.base('update',server,user)
	start = lambda self,server,user: self.base('start',server,user)
	stop = lambda self,server,user,force: {'protocal': 1,'type':'stop','data':{'server':server,'force':force,'user':{'id':user.id,'username':user.server,'discriminator':user.discriminator}}}
	restart = lambda self,server,user,force: {'protocal': 1,'type':'restart','data':{'server':server,'force':force,'user':{'id':user.id,'username':user.server,'discriminator':user.discriminator}}}
	ping = lambda self,server,user: self.base('ping',server,user)
	command = lambda self,server,user,command: {'protocal': 1,'type':'command','data':{'server':server,'command':command,'user':{'id':user.id,'username':user.server,'discriminator':user.discriminator}}}
	online = lambda self,server,user: self.base('online',server,user)
	reset = lambda self,server,user,banned_players,world: {'protocal': 1,'type':'reset','data':{'server':server,'banned_players':banned_players,'world':world,'user':{'id':user.id,'username':user.server,'discriminator':user.discriminator}}}
	size = lambda self,server,user: self.base('size',server,user)

class minecraft_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

	mc = SlashCommandGroup('mc','minecraft commands')

	async def send(self,ctx:ApplicationContext,server:str,packet:dict,always_give_response:bool=False,reply:bool=True) -> dict:
		try:
			with connect(f"ws://{self.client.db.guilds.read(ctx.guild.id,['mc_servers',server,'host'])}") as ws:
				await ws.send(dumps(packet))
				try: response = loads(await wait_for(ws.recv(),5))
				except TimeoutError:
					if reply: await ctx.followup.send('failed to connect to host: response timed out',ephemeral=await self.client.hide(ctx))
					return False
				if always_give_response: return response
				if response['success'][0]: return response
				else:
					if reply: await ctx.followup.send(f'error: {response["success"][1]}',ephemeral=await self.client.hide(ctx))
					return False
		except OSError:
			if reply: await ctx.followup.send('failed to connect to host: connection refused',ephemeral=await self.client.hide(ctx))
			return False

	async def ping(self,ctx:ApplicationContext,server:str,from_ping_command:bool=False) -> None:
		response = await self.send(ctx,server,packets.ping(server,ctx.author))
		if response is False: return False
		if from_ping_command: await ctx.followup.send(f'{server} ping: {response["data"]["ping"]}ms',ephemeral=await self.client.hide(ctx))
		return True

	@mc.command(
		name='add',
		description='connect a minecraft server to /reg/nal',
		options=[
			option(str,name='server',description='name of server. must match name in servers.json'),
			option(str,name='mc_regnal_host',description='ip:port of mc_regnal server')])
	# @has_perm('administrator')
	@has_perm('bot_owner')
	async def slash_mc_add(self,ctx:ApplicationContext,server:str,mc_regnal_host:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		# command can only be run by mc_regnal host
		# send add packet to mc_regnal
		# if success add server to db
		# else reply with error
		pass

	@mc.command(
		name='update',
		description='update an existing minecraft server',
		options=[
			option(str,name='server',description='name of server. must match name in servers.json')])
	# @has_perm('administrator')
	@has_perm('bot_owner')
	async def slash_mc_update(self,ctx:ApplicationContext,server:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		# command can only be run by mc_regnal host
		# send update packet to mc_regnal
		# if success update server in db
		# else reply with error
		pass

	@mc.command(
		name='remove',
		description='remove a minecraft server from /reg/nal',
		options=[
			option(str,name='server',description='server name')])
	# @has_perm('administrator')
	@has_perm('bot_owner')
	async def slash_mc_remove(self,ctx:ApplicationContext,server:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		# remove server from db
		pass

	@mc.command(
		name='start',
		description='start a minecraft server',
		options=[
			option(str,name='server',description='server name')])
	@has_perm('bot_owner')
	async def slash_mc_start(self,ctx:ApplicationContext,server:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		response = self.send(ctx,server,packets.start(server,ctx.author))
		if response is False: return
		await ctx.followup.send(f'started {server}',ephemeral=await self.client.hide(ctx))

	@mc.command(
		name='stop',
		description='stop a minecraft server',
		options=[
			option(str,name='server',description='server name'),
			option(bool,name='force',description='force stop even if players are online',requried=False,default=False)])
	@has_perm('bot_owner')
	async def slash_mc_stop(self,ctx:ApplicationContext,server:str,force:bool) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		if not await self.ping(ctx,server): return
		response = self.send(ctx,server,packets.stop(server,ctx.author,force))
		if response is False: return
		await ctx.followup.send(f'stopped {server}',ephemeral=await self.client.hide(ctx))

	@mc.command(
		name='restart',
		description='restart a minecraft server',
		options=[
			option(str,name='server',description='server name'),
			option(bool,name='force',description='force stop even if players are online',requried=False,default=False)])
	@has_perm('bot_owner')
	async def slash_mc_restart(self,ctx:ApplicationContext,server:str,force:bool) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		if not await self.ping(ctx,server): return
		response = self.send(ctx,server,packets.restart(server,ctx.author,force))
		if response is False: return
		await ctx.followup.send(f'restarted {server}',ephemeral=await self.client.hide(ctx))

	@mc.command(
		name='ping',
		description='ping a minecraft server',
		options=[
			option(str,name='server',description='server name')])
	@has_perm('bot_owner')
	async def slash_mc_ping(self,ctx:ApplicationContext,server:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		await self.ping(ctx,server,True)

	@mc.command(
		name='command',
		description='send a command to a minecraft server',
		options=[
			option(str,name='server',description='server name'),
			option(str,name='command',description='command')])
	@has_perm('bot_owner')
	async def slash_mc_command(self,ctx:ApplicationContext,server:str,command:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		if not await self.ping(ctx,server): return
		response = await self.send(ctx,server,packets.command(server,ctx.author,command))
		if response is False: return
		out = f'command "{command}" on {server}:\n```{response["data"]["command"]}```'
		if len(out) > 2000: await ctx.followup.send(f'{out[:1972]}\n\nMAX MESSAGE LENGTH REACHED',ephemeral=await self.client.hide(ctx))
		else: await ctx.followup.send(out,ephemeral=await self.client.hide(ctx))

	@mc.command(
		name='online',
		description='get the online players of a minecraft server',
		options=[
			option(str,name='server',description='server name')])
	@has_perm('bot_owner')
	async def slash_mc_online(self,ctx:ApplicationContext,server:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		if not await self.ping(ctx,server): return
		response = await self.send(ctx,server,packets.online(server,ctx.author))
		if not response: return
		embed = Embed(
			title=f'players on {server}',
			description=f'players online: {len(response["data"]["players"])}',
			color=await self.client.embed_color(ctx))
		if len(response["data"]["players"]) > 61: response["data"]["players"].insert(60,'...')
		embed.add_field(name='players',value='\n'.join(response["data"]["players"][:61]))
		await ctx.followup.send(embed=embed,ephemeral=await self.client.hide(ctx))

	@mc.command(
		name='reset',
		description='reset parts of a minecraft server',
		options=[
			option(str,name='server',description='server name'),
			option(bool,name='banned_players',description='banned players file',requried=False,default=False),
			option(bool,name='world',description='world folder',requried=False,default=False)])
	@has_perm('bot_owner')
	async def slash_mc_reset(self,ctx:ApplicationContext,server:str,banned_players:bool,world:bool) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		if self.ping(ctx,server):
			await ctx.followup.send('server cannot be reset while it is up')
			return
		response = await self.send(ctx,server,packets.reset(server,ctx.author,banned_players,world))
		if response is False: return
		reply = f'successfully reset {server} '
		if banned_players and world: reply += 'banned players file and world folder'
		elif banned_players: reply += 'banned players file'
		elif world: reply += 'world folder'
		else: reply = 'successfully reset nothing.'
		await ctx.followup.send(reply,ephmeral=await self.client.hide(ctx))
		
	@mc.command(
		name='list',
		description='list minecraft servers')
	@has_perm('bot_owner')
	async def slash_mc_list(self,ctx:ApplicationContext) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		servers = list((await self.client.db.guilds.read(ctx.guild.id,['mc_servers'])).keys())
		if len(servers) == 0: await ctx.followup.send('there are no minecraft servers here',ephemeral=await self.client.hide(ctx))
		else: await ctx.followup.send(embed=Embed(
			title='minecraft servers:',
			description='\n'.join(servers),
			color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@mc.command(
		name='info',
		description='get information about a specific minecraft server',
		options=[
			option(str,name='server',description='server name')])
	@has_perm('bot_owner')
	async def slash_mc_info(self,ctx:ApplicationContext,server:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		if not await self.ping(ctx,server): return
		server = await self.client.db.guilds.read(ctx.guild.id,['mc_servers',server])
		info = [
			f'ip: {server["ip"]}' if server['port'] == 25565 else f'ip: {server["ip"]}:{server["port"]}',
			f'version: {server["version"]}']
		if server['modpack'] is not None: info.append(f'modpack: {server["modpack"]}' if server['modpack_url'] is None else f'modpack: [{server["modpack"]}](<{server["modpack_url"]}>)')
		size = await self.send(ctx,server,packets.size(server,ctx.author,True),reply=False)
		if size: info.append(f'world size: {size["data"]["size"]}')

		await ctx.followup.send(embed=Embed(
			title=f'{server} info:',
			description='\n'.join(info),
			color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))



def setup(client:client_cls) -> None:
	client.add_cog(minecraft_cog(client))