from discord import Embed,ApplicationContext,Permissions,Guild,Message,Thread
from discord.commands import Option as option,SlashCommandGroup
from datetime import datetime,time as dtime,timedelta
from utils.tyrantlib import MakeshiftClass
from discord.errors import Forbidden
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from .shared import questions
from main import client_cls
from random import choice
from time import time


class qotd_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
		if 'DEV' in self.client.flags:
			self.qotd_loop.change_interval(time=(datetime.now()+timedelta(seconds=20)).astimezone(datetime.now().astimezone().tzinfo).timetz())
		self.qotd_loop.start()

	qotd = SlashCommandGroup('qotd','question of the day commands')

	async def _send_qotd(self,guild:Guild) -> tuple[Message|None,Thread|None]:
		doc = await self.client.db.guilds.read(guild.id,[])
		data:dict   = doc.get('data',{}).get('qotd',None)
		config:dict = doc.get('config',{}).get('qotd',None)
		if not config.get('enabled',False) or not config.get('channel',None): return (None,None)
		if next:=data.get('nextup',[]):
			question = next[0]
			await self.client.db.guilds.pop(guild.id,['data','qotd','nextup'],1)
		else:
			asked = data.get('asked',[])
			question = choice([q for q in questions if q not in asked]+data.get('pool',[]))
		msg = await guild.get_channel(config.get('channel',None)).send(
			embed=Embed(
				title='❓❔ Question of the Day ❔❓',
				description=question,
				color=await self.client.embed_color(MakeshiftClass(guild=guild))))
		save = [int(time()),msg.id]

		if config.get('spawn_threads',False):
			if config.get('delete_after',False):
				thread_name = 'qotd'
				if len(last:=data.get('last',[])) == 3:
					try: await guild.get_channel(config.get('channel',None)).get_thread(last[-1]).delete()
					except Forbidden:
						if guild.owner:
							await guild.owner.send(embed=Embed(title='permission error!',description='you enabled the `delete_after` QOTD option,\nbut /reg/nal does not have permission to delete threads,\nplease give him the `Manage Threads` permission, or disable the `delete_after` option',color=0xff6969))
							await self.client.log.debug(f'failed to create qotd thread for guild {guild.name}')
			else: thread_name = f'qotd-{datetime.now().strftime("%A.%d.%m.%y").lower()}'
			thread = await msg.create_thread(name=thread_name,auto_archive_duration=1440)
			save.append(thread.id)
			if role:=[i for i in msg.guild.roles if i.name.lower() == 'qotd' and not i.is_bot_managed()]:
				await thread.send(role[0].mention)

		await self.client.db.guilds.write(guild.id,['data','qotd','last'],save)
		await self.client.db.guilds.append(guild.id,['data','qotd','asked'],question)
		return msg

	@qotd.command(
		name='now',
		description='ask a question immediately | once per day',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True))
	async def slash_qotd_now(self,ctx:ApplicationContext) -> None:
		if time()-await self.client.db.guilds.read(ctx.guild.id,['data','qotd','last'])[0] < 86400:
			await ctx.response.send_message(embed=Embed(title='ERROR',description='it has not been 24 hours since the last question was asked!',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.defer(ephemeral=await self.client.hide(ctx))
		output = await self._send_qotd(ctx.guild)
		if None in output: return
		await ctx.followup.send(embed=Embed(title='success',description=f'read the question [here](<{output.jump_url}>)',color=await self.client.embed_color(ctx)),
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
				await self.client.db.guilds.append(ctx.guild.id,['data','qotd','nextup'],question)
				embed.add_field(name='added as next question, then discarded',value=question)
			case 'add as next question, then add to pool':
				await self.client.db.guilds.append(ctx.guild.id,['data','qotd','nextup'],question)
				await self.client.db.guilds.append(ctx.guild.id,['data','qotd','pool'],question)
				embed.add_field(name='added as next question, then added to pool',value=question)
			case 'add to question pool':
				await self.client.db.guilds.append(ctx.guild.id,['data','qotd','pool'],question)
				embed.add_field(name='added to question pool',value=question)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))

	@loop(time=dtime(9,0,tzinfo=datetime.now().astimezone().tzinfo))
	async def qotd_loop(self) -> None:
		for guild in self.client.guilds:
			try: await self._send_qotd(guild)
			except Exception as e: self.client.on_error(e)