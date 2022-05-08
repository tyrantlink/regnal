from discord.commands import SlashCommandGroup,Option as option
from discord import TextChannel,Role,ApplicationContext
from discord.ext.commands import Cog
from utils.tyrantlib import has_perm
from main import client_cls

class birthdays_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
	
	birthday = SlashCommandGroup('birthday','birthday commands')

	@birthday.command(
		name='setup',
		description='setup automatic birthday roles',
		options=[
			option(TextChannel,name='channel',description='birthday broadcast channel'),
			option(Role,name='role',description='birthday role')])
	@has_perm('manage_roles')
	async def slash_birthday_setup(self,ctx:ApplicationContext,channel:TextChannel,role:Role) -> None:
		if not await self.client.db.guilds.read(ctx.guild.id,['config','birthdays']): await ctx.response.send_message('birthdays are not enabled on this server. enable them with /config',ephemeral=await self.client.hide(ctx))
		await self.client.db.guilds.write(ctx.guild.id,['channels','birthday'],channel.id)
		await self.client.db.guilds.write(ctx.guild.id,['roles','birthday'],role.id)
		await ctx.response.send_message(f'successfully set birthday role to {role.mention} and birthday channel to {channel.mention}',ephemeral=await self.client.hide(ctx))
		await self.client.log

	@birthday.command(
		name='set',
		description='set your birthday',
		options=[
			option(int,name='month',description='month you were born'),
			option(int,name='day',description='day you were born'),
			option(bool,name='hide',description='hide from your user profile (you still get roles)')])
	async def slash_birthday_set(self,ctx:ApplicationContext,month:int,day:int,hide:bool) -> None:
		if month>12 or day>31:
			await ctx.response.send_message('invalid date.',ephemeral=True)
			return
		await self.client.db.users.write(ctx.author.id,['birthday'],f'{"h" if hide else ""}{str(month).zfill(2)}/{str(day).zfill(2)}')
		await ctx.response.send_message(f'successfully set birthday to {str(month).zfill(2)}/{str(day).zfill(2)}',ephemeral=True)
	
	@birthday.command(
		name='remove',
		description='remove your birthday')
	async def slash_birthday_remove(self,ctx:ApplicationContext) -> None:
		await self.client.db.users.write(ctx.author.id,['birthday'],None)
		await ctx.response.send_message('successfully removed birthday',ephemeral=True)


def setup(client:client_cls) -> None: client.add_cog(birthdays_cog(client))