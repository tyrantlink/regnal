from discord.commands import SlashCommandGroup,Option as option
from discord import User,ApplicationContext
from discord.ext.commands import Cog
from utils.tyrantlib import has_perm
from main import client_cls

class admin_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	admin = SlashCommandGroup('admin','admin commands')
	softban = admin.create_subgroup('softban','softban options (use /help for more details)')

	@softban.command(
		name='add',
		description='softban a user',
		options=[
			option(User,name='user',description='user to softban')])
	@has_perm('moderate_members')
	async def slash_admin_softban_add(self,ctx:ApplicationContext,user:User) -> None:
		await self.client.db.guilds.append(ctx.guild.id,['softbans'],user.id)
		await ctx.response.send_message(f'successfully softbanned {user.name}',ephemeral=await self.client.hide(ctx))
	
	@softban.command(
		name='remove',
		description='unsoftban a user',
		options=[
			option(User,name='user',description='user to unsoftban')])
	@has_perm('moderate_members')
	async def slash_admin_softban_remove(self,ctx:ApplicationContext,user:User) -> None:
		await self.client.db.guilds.remove(ctx.guild.id,['softbans'],user.id)
		await ctx.response.send_message(f'successfully unsoftbanned {user.name}',ephemeral=await self.client.hide(ctx))
	
	@admin.command(
		name='purge',
		description='purge message history',
		options=[
			option(int,name='messages',description='number of messages')])
	@has_perm('manage_messages')
	async def slash_admin_purge(self,ctx:ApplicationContext,messages:int) -> None:
		await ctx.channel.purge(limit=messages)
		await ctx.response.send_message(f'successfully purged {messages} messages',ephemeral=await self.client.hide(ctx))
	
	@admin.command(
		name='clear_activity_cache',
		description='use this if you deleted any invites')
	@has_perm('manage_guild')
	async def slash_admin_clear_activity_cache(self,ctx:ApplicationContext) -> None:
		await self.client.db.guilds.write(ctx.guild.id,['activity_cache'],{})
		await ctx.response.send_message(f'successfully cleared activity cache',ephemeral=await self.client.hide(ctx))

def setup(client:client_cls) -> None: client.add_cog(admin_cog(client))