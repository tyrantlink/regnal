from discord.commands import SlashCommandGroup,Option as option,slash_command
from discord import ApplicationContext,Permissions
from discord.ext.commands import Cog
from client import Client


class admin_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
	
	@slash_command(
		name='purge',
		description='purge message history',
		guild_only=True,default_member_permissions=Permissions(manage_messages=True),
		options=[
			option(int,name='messages',description='number of messages')])
	async def slash_admin_purge(self,ctx:ApplicationContext,messages:int) -> None:
		await ctx.channel.purge(limit=messages)
		await ctx.response.send_message(f'successfully purged {messages} messages',ephemeral=await self.client.hide(ctx))

def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(admin_commands(client))