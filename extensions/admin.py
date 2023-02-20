from discord import ApplicationContext,Permissions,Embed,Object
from discord.commands import Option as option,slash_command
from discord.ext.commands import Cog
from discord.errors import Forbidden
from client import Client


class admin_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	@slash_command(
		name='purge',
		description='purge message history',
		guild_only=True,default_member_permissions=Permissions(manage_messages=True),
		options=[
			option(int,name='messages',description='number of messages',required=False,default=None),
			option(str,name='message_id',description='message id, all messages until (but not including) given id will be deleted',required=False,default=None)])
	async def slash_admin_purge(self,ctx:ApplicationContext,messages:int=None,message_id:str=None) -> None:
		if messages is None and message_id is None:
			await ctx.response.send_message(embed=Embed(title='ERROR',description='you must specify either message count or message_id',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
			return
		if messages is not None and message_id is not None:
			await ctx.response.send_message(embed=Embed(title='ERROR',description='you must specify either message count or message_id, not both',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.defer(ephemeral=await self.client.hide(ctx))
		if messages:
			try: purged = await ctx.channel.purge(limit=messages,reason=f'{ctx.author.name} used purge command')
			except Forbidden:
				await ctx.followup.send(embed=Embed(title='PERMISSION ERROR',description='i am missing either `Manage Messages` or `Read Message History`\nbe sure to check both my integration role and channel overrides',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
				return
		if message_id:
			try: message = Object(message_id)
			except TypeError:
				await ctx.followup.send(embed=Embed(title='ERROR',description='invalid message_id given',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
				return
			try: purged = await ctx.channel.purge(limit=None,after=message.created_at,reason=f'{ctx.author.name} used purge command')
			except Forbidden:
				await ctx.followup.send(embed=Embed(title='PERMISSION ERROR',description='i am missing either `Manage Messages` or `Read Message History`\nbe sure to check both my integration role and channel overrides',color=0xff6969),
				ephemeral=await self.client.hide(ctx))
				return
		await ctx.followup.send(embed=Embed(title=f'successfully purged {len(purged)} messages',color=await self.client.embed_color(ctx)),ephemeral=await self.client.hide(ctx))

def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(admin_commands(client))