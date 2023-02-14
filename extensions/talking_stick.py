from discord import Embed,ApplicationContext,Guild,Permissions,Member
from discord.commands import SlashCommandGroup
from datetime import datetime,time as dtime
from utils.tyrantlib import MakeshiftClass
from discord.ext.commands import Cog
from discord.errors import NotFound
from discord.ext.tasks import loop
from client import Client
from random import choice


class talking_stick_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.talking_stick_loop.start()

	stick = SlashCommandGroup('stick','talking stick commands')

	async def check(self,ctx:ApplicationContext) -> bool:
		if not await self.client.db.guild(ctx.guild.id).config.talking_stick.enabled.read():
			await ctx.response.send_message('the talking stick is not enabled on this server. enable it with /config',ephemeral=await self.client.hide(ctx))
			return False
		return True

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

		for id in await self.client.db.guild(ctx.guild.id).data.talking_stick.active.read():
			line = f'{await self.client.db.user(int(id)).username.read()}'
			if len(f'{nl.join(output)}\n{line}') > 1980: break
			output.append(line)

		await ctx.followup.send(
			embed=Embed(
				title='Talking Stick Leaderboard:',
				description=nl.join(output),
				color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	async def roll_talking_stick(self,guild:Guild) -> None:
		guild_data = await self.client.db.guild(guild.id).read()
		role = guild.get_role(guild_data.get('config',{}).get('talking_stick',{}).get('role'))
		active_members = guild_data.get('data',{}).get('talking_stick',{}).get('active')
		old_stick = guild_data.get('data',{}).get('talking_stick',{}).get('current_stick',None)
		if len(active_members) == 0: return
		for attempt in range(15):
			rand:Member = choice(active_members)
			# continue if repeat user
			if old_stick == rand: continue
			if not await self.client.db.user(rand).config.general.talking_stick.read(): continue
			try: member = await guild.fetch_member(rand)
			except NotFound: continue
			if member.bot: continue
			break
		else: return

		for old_member in role.members: await old_member.remove_roles(role)
		await member.add_roles(role)
		await self.client.db.guild(guild.id).data.talking_stick.current_stick.write(rand)
		await self.client.db.guild(guild.id).data.leaderboards.sticks.inc(1,[str(rand)])
		await self.client.db.guild(guild.id).data.talking_stick.active.write([])

		await (guild.get_channel(guild_data.get('config',{}).get('talking_stick',{}).get('channel'))).send(
			f'congrats {member.mention} you have the talking stick.',
			embed=Embed(
				title=f'chances: 1/{len(active_members)}',
				description='\n'.join([f'<@!{member_id}>' if member_id != rand else f'>>><@!{member_id}><<<' for member_id in active_members]),
				color=await self.client.embed_color(MakeshiftClass(guild=guild))))

		await self.client.log.talking_stick(MakeshiftClass(guild=guild,user=member))

	@loop(time=dtime(9,0,tzinfo=datetime.now().astimezone().tzinfo))
	async def talking_stick_loop(self) -> None:
		for guild in self.client.guilds:
			try:
				data = await self.client.db.guild(guild.id).config.talking_stick.read()
				if not data['enabled'] or not data['role'] or not data['channel']: continue
				await self.roll_talking_stick(guild)
			except Exception as error:
				continue

def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(talking_stick_commands(client))