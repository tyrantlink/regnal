from discord import Role,TextChannel,Embed,ApplicationContext,Guild,Permissions,Member
from discord.commands import Option as option,SlashCommandGroup
from utils.tyrantlib import MakeshiftClass
from discord.ext.commands import Cog
from discord.errors import NotFound
from discord.ext.tasks import loop
from datetime import datetime
from main import client_cls
from random import choice


class talking_stick_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.talking_stick_loop.start()
	
	stick = SlashCommandGroup('stick','talking stick commands')
	
	async def check(self,ctx:ApplicationContext) -> bool:
		if not await self.client.db.guilds.read(ctx.guild.id,['config','talking_stick','enabled']):
			await ctx.response.send_message('the talking stick is not enabled on this server. enable it with /config',ephemeral=await self.client.hide(ctx))
			return False
		return True

	# @stick.command(
	# 	name='setup',
	# 	description='setup the talking stick',
	# 	guild_only=True,default_member_permissions=Permissions(manage_guild=True,manage_roles=True),
	# 	options=[
	# 		option(Role,name='role',description='talking stick role'),
	# 		option(TextChannel,name='channel',description='talking stick broadcast channel'),
	# 		option(Role,name='limit_role',description='required role to be eligible for talking stick',default=None,required=False)])
	# async def slash_stick_setup(self,ctx:ApplicationContext,role:Role,channel:TextChannel,limit_role:Role) -> None:	

	# 	if not await self.check(ctx): return
		
	# 	await self.client.db.guilds.write(ctx.guild.id,['roles','talking_stick'],role.id)
	# 	await self.client.db.guilds.write(ctx.guild.id,['channels','talking_stick'],channel.id)
	# 	await self.client.db.guilds.write(ctx.guild.id,['roles','talking_stick_limit'],limit_role.id)

	# 	await ctx.response.send_message(f'successfully set channel to {channel.name} and role to {role.mention}',ephemeral=await self.client.hide(ctx))

	@stick.command(
		name='reroll',
		description='force reroll the talking stick',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True,manage_roles=True))
	async def slash_stick_reroll(self,ctx:ApplicationContext) -> None:
		if not await self.check(ctx): return
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		await self.roll_talking_stick(ctx.guild)
		await ctx.followup.send('reroll successful',ephemeral=await self.client.hide(ctx))

	@stick.command(
		name='active',
		description='list daily active members')
	async def slash_stick_active(self,ctx:ApplicationContext) -> None:
		if not await self.check(ctx): return
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		output,nl = [],'\n'

		for id in await self.client.db.guilds.read(ctx.guild.id,['data','talking_stick','active']):
			line = f'{await self.client.db.users.read(int(id),["username"])}'
			if len(f'{nl.join(output)}\n{line}') > 1980: break
			output.append(line)

		await ctx.followup.send(
			embed=Embed(
				title='Talking Stick Leaderboard:',
				description=nl.join(output),
				color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	async def roll_talking_stick(self,guild:Guild) -> None:
		role = guild.get_role(await self.client.db.guilds.read(guild.id,['config','talking_stick','role']))
		active_members = await self.client.db.guilds.read(guild.id,['data','talking_stick','active'])
		if len(active_members) == 0: return
		for attempt in range(15):
			rand:Member = choice(active_members)
			if not await self.client.db.users.read(rand,['config','talking_stick']): continue
			old_stick = await self.client.db.guilds.read(guild.id,['data','talking_stick','current_stick'])
			if old_stick == rand: continue # continue if repeat user
			try: member = await guild.fetch_member(rand)
			except NotFound: continue
			if member.bot: continue
			break
		else: return

		for old_member in role.members: await old_member.remove_roles(role)
		await member.add_roles(role)
		await self.client.db.guilds.write(guild.id,['data','talking_stick','current_stick'],rand)
		await self.client.db.guilds.inc(guild.id,['data','leaderboards','sticks',str(rand)])
		await self.client.db.guilds.write(guild.id,['data','talking_stick','active'],[])
		
		await (guild.get_channel(await self.client.db.guilds.read(guild.id,['config','talking_stick','channel']))).send(
			f'congrats {member.mention} you have the talking stick.',
			embed=Embed(
				title=f'chances: 1/{len(active_members)}',
				description='\n'.join([f'<@!{member_id}>' if member_id != rand else f'>>><@!{member_id}><<<' for member_id in active_members]),
				color=await self.client.db.guilds.read(guild.id,['config','general','embed_color'])))

		await self.client.log.talking_stick(MakeshiftClass(guild=guild,user=member))

	@loop(minutes=1)
	async def talking_stick_loop(self) -> None:
		if datetime.now().strftime("%H:%M") == '09:00':
			for guild in self.client.guilds:
				try:
					data = await self.client.db.guilds.read(guild.id,['config','talking_stick'])
					if not data['enabled'] or not data['role'] or not data['channel']: continue
					await self.roll_talking_stick(guild)
				except Exception as error:
					continue