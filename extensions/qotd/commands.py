from discord import TextChannel,Embed,ApplicationContext,Permissions,Guild,Message,Thread
from discord.commands import Option as option,SlashCommandGroup
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from datetime import datetime
from .shared import questions
from main import client_cls
from random import choice
from time import time

class qotd_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		self.qotd_loop.start()

	qotd = SlashCommandGroup('qotd','question of the day commands')

	async def _send_qotd(self,guild:Guild) -> tuple[Message|None,Thread|None]:
		data = await self.client.db.guilds.read(guild.id,[])
		if not data['config']['qotd'] or not data['channels']['qotd']: return (None,None)
		if data['qotd']['nextup']:
			question = data['qotd']['nextup'][0]
			await self.client.db.guilds.pop(guild.id,['qotd','nextup'],1)
		else:
			question = choice(questions+data['qotd']['pool'])
		msg = await guild.get_channel(data['channels']['qotd']).send(
			embed=Embed(
				title='❓❔ Question of the Day ❔❓',
				description=question,
				color=await self.client.db.guilds.read(guild.id,['config','embed_color'])))
		thread = await msg.create_thread(name=f'qotd-{datetime.now().strftime("%A.%d.%m.%y").lower()}',auto_archive_duration=1440)
		if role:=[i for i in msg.guild.roles if i.name.lower() == 'qotd' and not i.is_bot_managed()]:
			await thread.send(role[0].mention)
		await self.client.db.guilds.write(guild.id,['data','last_qotd'],int(time()))
		return (msg,thread)

	@qotd.command(
		name='setup',
		description='setup the question of the day',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True),
		options=[
			option(TextChannel,name='channel',description='qotd question channel')])
	async def slash_qotd_setup(self,ctx:ApplicationContext,channel:TextChannel) -> None:
		if not channel.can_send():
			await ctx.response.send_message(embed=Embed(title='ERROR',description='/reg/nal must be able to send messages in this channel.\nplease fix the permissions and try again.',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.defer(ephemeral=await self.client.hide(ctx))
		response = Embed(title='QOTD setup complete!',description='/reg/nal will ping any role named qotd, bringing all users with that role into the thread\nconsider making a role menu with /role_menu to allow users to self-assign a role',color=await self.client.embed_color(ctx))
		response.add_field(name='channel',value=channel.mention,inline=False)

		if not await self.client.db.guilds.read(ctx.guild.id,['config','qotd']):
			await self.client.db.guilds.write(ctx.guild.id,['config','qotd'],True)
			response.add_field(name='warning!',value='qotd was disabled in config, it has been enabled for your convenience\nif you wish to disable it, run `/config`',inline=False)
		if not time()-await self.client.db.guilds.read(ctx.guild.id,['data','last_qotd']) < 86400:
			response.add_field(name='ask the first question!',value='run the command `/qotd now` to ask a question immediately, or you can wait until <t:1669568400:t> for the question to be automatically asked.',inline=False)

		await self.client.db.guilds.write(ctx.guild.id,['channels','qotd'],channel.id)
		await ctx.followup.send(embed=response,ephemeral=await self.client.hide(ctx))

	@qotd.command(
		name='now',
		description='ask a question immediately | once per day',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True))
	async def slash_qotd_now(self,ctx:ApplicationContext) -> None:
		if time()-await self.client.db.guilds.read(ctx.guild.id,['data','last_qotd']) < 86400:
			await ctx.response.send_message(embed=Embed(title='ERROR',description='it has not been 24 hours since the last question was asked!',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.defer(ephemeral=await self.client.hide(ctx))
		output = await self._send_qotd(ctx.guild)
		if None in output: return
		await ctx.followup.send(embed=Embed(title='success',description=f'read the question [here](<{output[0].jump_url}>)',color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@qotd.command(
		name='add_question',
		description='add a custom question',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True),
		options=[
			option(str,name='type',description='ask as next question or add to question pool?',
				choices=['add as next question','add as next question, then add to pool','add to question pool']),
			option(str,name='question',description='question to be asked',max_length=1024)])
	async def slash_qotd_add_question(self,ctx:ApplicationContext,type:str,question:str) -> None:
		embed = Embed(title='successfully added a qotd question',color=await self.client.embed_color(ctx))
		match type:
			case 'add as next question':
				await self.client.db.guilds.append(ctx.guild.id,['qotd','nextup'],question)
				embed.add_field(name='added as next question, then discarded',value=question)
			case 'add as next question, then add to pool':
				await self.client.db.guilds.append(ctx.guild.id,['qotd','nextup'],question)
				await self.client.db.guilds.append(ctx.guild.id,['qotd','pool'],question)
				embed.add_field(name='added as next question, then added to pool',value=question)
			case 'add to question pool':
				await self.client.db.guilds.append(ctx.guild.id,['qotd','pool'],question)
				embed.add_field(name='added to question pool',value=question)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))

	@loop(minutes=1)
	async def qotd_loop(self) -> None:
		if datetime.now().strftime("%H:%M") == '09:00':
			for guild in self.client.guilds:
				try: await self._send_qotd(guild)
				except Exception: continue