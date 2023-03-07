from discord import Embed,Permissions,Guild,Message,Thread,User,Interaction
from utils.classes import MakeshiftClass,ApplicationContext,EmptyView
from discord.commands import Option as option,SlashCommandGroup
from datetime import datetime,time as dtime,timedelta
from discord.errors import Forbidden,NotFound
from utils.tyrantlib import dev_banned
from discord.ext.commands import Cog
from discord.ui import Button,button
from ._shared_vars import questions
from discord.ext.tasks import loop
from client import Client
from random import choice
from time import time


class qotd_new_log_view(EmptyView):
	def __init__(self,client:Client) -> None:
		super().__init__(timeout=None)
		self.client = client
		self.add_item(self.remove_button)

	@button(
		label='remove',style=4,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		embed_data = interaction.message.embeds[0].fields[0].to_dict()
		category,question = embed_data.get('name',None),embed_data.get('value',None)
		match category:
			case 'added as next question, then discarded':
				await self.client.db.guild(interaction.guild.id).data.qotd.nextup.remove(question)
			case 'added as next question, then added to pool':
				await self.client.db.guild(interaction.guild.id).data.qotd.nextup.remove(question)
				await self.client.db.guild(interaction.guild.id).data.qotd.pool.remove(question)
			case 'added to question pool':
				await self.client.db.guild(interaction.guild.id).data.qotd.pool.remove(question)
		new_embed = interaction.message.embeds[0]
		new_embed.description = f'**REMOVED BY {interaction.user.mention}**'
		await interaction.response.edit_message(embed=new_embed,view=None)
		await interaction.followup.send('successfully removed question',ephemeral=True)

class qotd_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		if 'DEV' in self.client.flags.keys():
			self.qotd_loop.change_interval(time=(datetime.now()+timedelta(seconds=20)).astimezone(datetime.now().astimezone().tzinfo).timetz())
		self.qotd_loop.start()
		self.client.add_view(qotd_new_log_view(self.client))

	def cog_unload(self) -> None:
		self.qotd_loop.cancel()

	qotd = SlashCommandGroup('qotd','question of the day commands')

	async def _dm_error(self,user:User,title:str,description:str) -> None:
		await user.send(embed=Embed(title=title,description=description,color=0xff6969))

	async def _send_qotd(self,guild:Guild) -> tuple[Message|None,Thread|None]:
		doc = await self.client.db.guild(guild.id).read()
		if doc is None: return
		data:dict   = doc.get('data',{}).get('qotd',None)
		config:dict = doc.get('config',{}).get('qotd',None)
		if not config.get('enabled',False) or not config.get('channel',None): return None
		if next:=data.get('nextup',[]):
			question = next[0]
			await self.client.db.guild(guild.id).data.qotd.nextup.pop(1)
		else:
			asked = data.get('asked',[])
			pool = [q for q in questions+data.get('pool',[]) if q not in asked]
			if pool == []:
				pool = questions+data.get('pool',[])
				await self.client.db.guild(guild.id).data.qotd.asked.write([])
			question = choice(pool)

		embed = Embed(
			title='❓❔ Question of the Day ❔❓',
			description=question,
			color=await self.client.embed_color(MakeshiftClass(guild=guild)))
		channel = guild.get_channel(config.get('channel',None))
		roles = [i for i in guild.roles if i.name.lower() == 'qotd' and not i.is_bot_managed()]
		role = roles[0].mention if roles else None

		match str(channel.type):
			case 'text': msg = await channel.send(role,embed=embed)
			case 'forum':
				try:
					if (old_thread:=channel.get_thread(data.get('last',[])[-1])) is not None:
						await old_thread.edit(archived=True,locked=True,pinned=False)
				except AttributeError: pass
				except Forbidden:
					if guild.owner:
						await self._dm_error(guild.owner,'permission error!','/reg/nal failed to archive the last QOTD thread, please give him the `Manage Threads` permission')
						await self.client.log.debug(f'failed to create qotd thread for guild {guild.name}')
				msg = await channel.create_thread(
					name=question if len(question) <= 100 else f'{question[:97]}...',
					content=role,
					embed=embed,
					auto_archive_duration=1440)
				await msg.edit(pinned=True)
			case _:
				await self._dm_error(guild.owner,'channel error!',f'the QOTD channel must be set to either a text channel or a forum channel,\nit is a currently set to a {channel.type} channel')
				return
		await self.client.db.guild(guild.id).data.qotd.last.write([int(time()),msg.id])
		await self.client.db.guild(guild.id).data.qotd.asked.append(question)
		return msg

	@qotd.command(
		name='now',
		description='ask a question immediately | once per day',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True))
	async def slash_qotd_now(self,ctx:ApplicationContext) -> None:
		if time()-(await self.client.db.guild(ctx.guild.id).data.qotd.last.read())[0] < 86400:
			await ctx.response.send_message(embed=Embed(title='ERROR',description='it has not been 24 hours since the last question was asked!',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
			return
		output = await self._send_qotd(ctx.guild)
		await ctx.response.defer(ephemeral=await self.client.hide(ctx))
		if output is None:
			await ctx.followup.send(embed=Embed(title='ERROR',description=f'i failed to send the QOTD message.\nis it enabled in </config:{self.client.get_application_command("config").id}> and is there a channel set?',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
			return
		await ctx.followup.send(embed=Embed(title='success',description=f'read the question [here](<{output.jump_url}>)' if output else None,color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@qotd.command(
		name='add_question',
		description='add a custom question',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True),
		options=[
			option(str,name='type',description='ask as next question or add to question pool?',
				choices=['add as next question','add as next question, then add to pool','add to question pool']),
			option(str,name='question',description='question to be asked',max_length=1024)])
	@dev_banned()
	async def slash_qotd_add_question(self,ctx:ApplicationContext,type:str,question:str) -> None:
		embed = Embed(title='successfully added a qotd question',color=await self.client.embed_color(ctx))
		log_embed = Embed(color=await self.client.embed_color(ctx))
		match type:
			case 'add as next question':
				await self.client.db.guild(ctx.guild.id).data.qotd.nextup.append(question)
				embed.add_field(name='added as next question, then discarded',value=question)
				log_embed.add_field(name='added as next question, then discarded',value=question)
			case 'add as next question, then add to pool':
				await self.client.db.guild(ctx.guild.id).data.qotd.nextup.append(question)
				await self.client.db.guild(ctx.guild.id).data.qotd.pool.append(question)
				embed.add_field(name='added as next question, then added to pool',value=question)
				log_embed.add_field(name='added as next question, then added to pool',value=question)
			case 'add to question pool':
				await self.client.db.guild(ctx.guild.id).data.qotd.pool.append(question)
				embed.add_field(name='added to question pool',value=question)
				log_embed.add_field(name='added to question pool',value=question)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))
		if log_channel:=await self.client.db.guild(ctx.guild.id).config.logging.channel.read():
			try: channel = ctx.guild.get_channel(log_channel) or await ctx.guild.fetch_channel(log_channel)
			except (NotFound,Forbidden): return
			log_embed.set_author(name=f'{ctx.author.display_name} used /qotd add_question',icon_url=ctx.author.display_avatar.url)
			await channel.send(embed=log_embed,view=qotd_new_log_view(self.client))

	@loop(time=dtime(9,0,tzinfo=datetime.now().astimezone().tzinfo))
	async def qotd_loop(self) -> None:
		for guild in self.client.guilds:
			try: await self._send_qotd(guild)
			except Exception as e: await self.client.on_error(e)

def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(qotd_commands(client))

# async def teardown(client:Client) -> None:
