from discord import ApplicationContext,TextChannel,Embed,Permissions
from discord.commands import SlashCommandGroup,Option as option
from discord.utils import escape_markdown
from discord.ext.commands import Cog
from main import client_cls

class admin_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

	admin = SlashCommandGroup('admin','admin commands')
	
	@admin.command(
		name='purge',
		description='purge message history',
		guild_only=True,default_member_permissions=Permissions(manage_messages=True),
		options=[
			option(int,name='messages',description='number of messages')])
	async def slash_admin_purge(self,ctx:ApplicationContext,messages:int) -> None:
		await ctx.channel.purge(limit=messages)
		await ctx.response.send_message(f'successfully purged {messages} messages',ephemeral=await self.client.hide(ctx))
	
	@admin.command(
		name='clear_activity_cache',
		description='use this if you deleted any invites',
		guild_only=True,default_member_permissions=Permissions(manage_guild=True))
	async def slash_admin_clear_activity_cache(self,ctx:ApplicationContext) -> None:
		await self.client.db.guilds.write(ctx.guild.id,['activity_cache'],{})
		await ctx.response.send_message(f'successfully cleared activity cache',ephemeral=await self.client.hide(ctx))
	
	@admin.command(name='filter',
		description='filter messages with regex',
		guild_only=True,default_member_permissions=Permissions(manage_messages=True),
		options=[
			option(str,name='location',description='guild-wide or specific channel',choices=['guild','channel']),
			option(str,name='mode',description='add, remove or list filters',choices=['add','remove','list']),
			option(str,name='filter',description='regex filter',optional=True,default=None),
			option(TextChannel,name='channel',description='channel. current channel if left empty',optional=True,default=None)])
	async def admin_filter(self,ctx:ApplicationContext,location:str,mode:str,filter:str|None,channel:TextChannel|None) -> None:
		if location == 'channel' and channel is None: channel = ctx.channel
		match mode:
			case 'add':
				if filter is None:
					await ctx.response.send_message('you must specify a filter to add.',ephemeral=await self.client.hide(ctx))
				match location:
					case 'guild': await self.client.db.guilds.append(ctx.guild.id,['regex','guild'],filter)
					case 'channel': await self.client.db.guilds.append(ctx.guild.id,['regex','channel',str(channel.id)],filter)
					case _: await ctx.response.send_message('invalid location, how did you even do that?',ephemeral=await self.client.hide(ctx))
				await ctx.response.send_message(f'successfully added {escape_markdown(filter)} to the {location if location == "guild" else channel.mention} filter list.',ephemeral=await self.client.hide(ctx))
			case 'remove':
				if filter is None:
					await ctx.response.send_message('you must specify a filter to remove.',ephemeral=await self.client.hide(ctx))
				match location:
					case 'guild': await self.client.db.guilds.remove(ctx.guild.id,['regex','guild'],filter)
					case 'channel': await self.client.db.guilds.remove(ctx.guild.id,['regex','channel',str(channel.id)],filter)
					case _: await ctx.response.send_message('invalid location, how did you even do that?',ephemeral=await self.client.hide(ctx))
				await ctx.response.send_message(f'successfully removed {escape_markdown(filter)} from the {location if location == "guild" else channel.mention} filter list.',ephemeral=await self.client.hide(ctx))
			case 'list': 
				match location:
					case 'guild': res = await self.client.db.guilds.read(ctx.guild.id,['regex','guild'])
					case 'channel': res = await self.client.db.guilds.read(ctx.guild.id,['regex','channel',str(channel.id)])
					case _: res = []
				await ctx.response.send_message(embed=Embed(title=f'current {location} filters regex' if res else f'no {channel} regex filters set',description=escape_markdown('\n'.join(res))),ephemeral=await self.client.hide(ctx))

			case _: await ctx.response.send_message('invalid mode, how did you even do that?',ephemeral=await self.client.hide(ctx))

def setup(client:client_cls) -> None: client.add_cog(admin_cog(client))