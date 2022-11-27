from discord import TextChannel,Embed,ApplicationContext,Permissions
from discord.commands import Option as option,SlashCommandGroup
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from datetime import datetime
from main import client_cls
from random import choice

class qotd_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client
		self.qotd_loop.start()

	qotd = SlashCommandGroup('qotd','question of the day commands')

	async def check(self,ctx:ApplicationContext) -> bool:
		if not await self.client.db.guilds.read(ctx.guild.id,['config','qotd']):
			await ctx.response.send_message('qotd is not enabled on this server. enable it with /config',ephemeral=await self.client.hide(ctx))
			return False
		return True

	@qotd.command(
		name='setup',
		description='setup the question of the day',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True),
		options=[
			option(TextChannel,name='channel',description='qotd question channel')])
	async def slash_qotd_setup(self,ctx:ApplicationContext,channel:TextChannel) -> None:
		if not await self.check(ctx): return
		await self.client.db.guilds.write(ctx.guild.id,['channels','qotd'],channel.id)
		await ctx.response.send_message(
			f'setup complete.\nchannel: {channel.mention}',
			ephemeral=await self.client.hide(ctx))

	@qotd.command(
		name='add_question',
		description='add a custom question',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True),
		options=[
			option(str,name='type',description='ask as next question or add to question pool?',
				choices=['add as next question','add as next question, then add to pool','add to question pool']),
			option(str,name='question',description='question to be asked')])
	async def slash_qotd_add_question(self,ctx:ApplicationContext,type:str,question:str) -> None:
		match type:
			case 'add as next question':
				await self.client.db.guilds.append(ctx.guild.id,['qotd','nextup'],question)
			case 'add as next question, then add to pool':
				await self.client.db.guilds.append(ctx.guild.id,['qotd','nextup'],question)
				await self.client.db.guilds.append(ctx.guild.id,['qotd','pool'],question)
			case 'add to question pool':
				await self.client.db.guilds.append(ctx.guild.id,['qotd','pool'],question)
		await ctx.response.send_message('successfully added question.',ephemeral=await self.client.hide(ctx))

	@loop(minutes=1)
	async def qotd_loop(self) -> None:
		if datetime.now().strftime("%H:%M") == '09:00':
			thread_name = f'qotd-{datetime.now().strftime("%A").lower()}'
			for guild in self.client.guilds:
				try:
					data = await self.client.db.guilds.read(guild.id,[])
					if not data['config']['qotd'] or not data['channels']['qotd']: continue
					if data['qotd']['nextup']:
						question = data['qotd']['nextup'][0]
						await self.client.db.guilds.pop(guild.id,['qotd','nextup'],1)
					else:
						with open('content/qotd') as file:
							question = choice(file.readlines()+data['qotd']['pool'])
					msg = await guild.get_channel(data['channels']['qotd']).send(
						embed=Embed(
							title='❓❔ Question of the Day ❔❓',
							description=question,
							color=await self.client.db.guilds.read(guild.id,['config','embed_color'])))
					await msg.create_thread(name=thread_name,auto_archive_duration=1440)
				except Exception: continue


def setup(client:client_cls) -> None: client.add_cog(qotd_cog(client))