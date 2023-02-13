from discord import User,File,Message,ApplicationContext,Permissions,Embed
from discord.commands import SlashCommandGroup,Option as option
from discord.ext.commands import Cog,message_command
from client import Client
from .utils import utils
from io import StringIO
from json import dumps
from time import time


class logging_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.utils = utils(client)

	logging = SlashCommandGroup('logging','logging commands',guild_only=True,default_member_permissions=Permissions(view_audit_log=True))

	@logging.command(name='get',
		description='get logs from message by id',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True),
		options=[
			option(str,name='message_id',description='in the footer of logs'),
			option(bool,name='raw',description='show the raw, not pretty unformatted log',required=False,default=False)])
	async def slash_logging_get(self,ctx:ApplicationContext,message_id:str,raw:bool):
		log = await self.client.db.message(int(message_id)).read()
		if log is None or log.get('guild',None) != ctx.guild.id:
			await ctx.response.send_message(embed=Embed(title='no logs found.',color=0xffff69),ephemeral=await self.client.hide(ctx))
			return
		if raw:
			log = dumps(log,indent=2)
			if len(log)+12 > 2000: await ctx.response.send_message(file=File(StringIO(log),f'log{message_id}.txt'))
			else: await ctx.response.send_message(f'```json\n{log}\n```')
		else: await ctx.response.send_message(embed=await self.utils.gen_embed(ctx.guild,int(message_id)),ephemeral=await self.client.hide(ctx))

	@logging.command(name='recent',
		description='get ten most recent logs',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True),
		options=[option(User,name='user',description='limit to logs from a specific user',required=False)])
	async def slash_logging_recent(self,ctx:ApplicationContext,user:User) -> None:
		data = [doc async for doc in self.client.db.message(0).__col.find(
			{'guild':ctx.guild.id} if user is None else {'guild':ctx.guild.id,'author':user.id},sort=[('_id',-1)],limit=10)]

		if data == []:
			await ctx.response.send_message(f'no logs found',ephemeral=True)
			return

		await ctx.response.send_message(embeds=[await self.utils.gen_embed(ctx.guild,doc.get('_id'),doc=doc) for doc in data],ephemeral=await self.client.hide(ctx))

	@logging.command(name='all',
		description='get a file with all log history. one use per day.',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True,manage_guild=True),
		options=[
			option(str,name='sorting',description='sorting order',choices=['newest first','oldest first'])])
	async def slash_logging_all(self,ctx:ApplicationContext,sorting:str) -> None:
		await ctx.defer(ephemeral=True)
		if time()-(last_history:=await self.client.db.guild(ctx.guild.id).data.logging.last_history.read()) < 86400:
			await ctx.followup.send(embed=Embed(title='you cannot use this command again until 24 hours have passed.',
				description=f'you can use the command again <t:{last_history+86400}:R>'),ephemeral=True)
			return

		data = [doc async for doc in self.client.db.message(0).__col.find({'guild_id':ctx.guild.id},sort=[('_id',-1 if sorting == 'newest first' else 1)])]
		data.insert(0,f'total entries: {len(data)}')

		if data == []:
			await ctx.followup.send(f'no logs found',ephemeral=True)
			return

		await ctx.followup.send('all logs',file=File(StringIO(dumps(data,indent=2)),'history.json'),ephemeral=True)
		await self.client.db.guild(ctx.guild.id).data.logging.last_history.write(time())

	@message_command(
		name='message logs',
		guild_only=True,default_member_permissions=Permissions(view_audit_log=True))
	async def message_message_logs(self,ctx:ApplicationContext,message:Message) -> None:
		log:dict = await self.client.db.message(int(message.id)).read()
		if log is None or log.get('author',None) == self.client.user.id:
			log = await self.client.db.message(0).__col.find_one({'log_messages':message.id}) or log
		if log is None or log.get('guild',None) != ctx.guild.id:
			await ctx.response.send_message(embed=Embed(title='no logs found.',color=0xffff69),ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.send_message(embed=await self.utils.gen_embed(ctx.guild,log.get('_id',message.id)),ephemeral=await self.client.hide(ctx))