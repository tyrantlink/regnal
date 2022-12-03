from discord import ApplicationContext,Embed,Permissions,Member,InputTextStyle
from discord.commands import slash_command,Option as option
from .modals import auto_response_modal
from discord.ext.commands import Cog
from discord.ui import InputText
from .shared import c_au_choices
from main import client_cls


class auto_response_commands(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	@slash_command(
		name='auto_response',
		description='add the current channel to the whitelist or blacklist',
		guild_only=True,default_member_permissions=Permissions(manage_channels=True),
		options=[option(str,name='option',description='auto_response commands',choices=['add','remove','list'])])
	async def slash_auto_response(self,ctx:ApplicationContext,option:str):
		au_cfg = await self.client.db.guilds.read(ctx.guild.id,['config','auto_responses','enabled'])
		match option:
			case 'add'|'remove':
				match au_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'auto responses are currently {au_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						if option == 'add':
							await self.client.db.guilds.append(ctx.guild.id,['data','auto_responses',au_cfg],ctx.channel.id)
							res = ('added','to')
						else:
							await self.client.db.guilds.remove(ctx.guild.id,['data','auto_responses',au_cfg],ctx.channel.id)
							res = ('removed','from')
						await ctx.response.send_message(f'successfully {res[0]} {ctx.channel.mention} {res[1]} the {au_cfg}.',ephemeral=await self.client.hide(ctx))
					case _: raise
			case 'list':
				match au_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'auto responses are currently {au_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						await ctx.response.send_message(embed=Embed(title=au_cfg,description='\n'.join([str(i) for i in await self.client.db.guilds.read(ctx.guild.id,['data','auto_responses',au_cfg])])),ephemeral=await self.client.hide(ctx))
					case _: raise
			case _: raise
	
	@slash_command(
		name='dad_bot',
		description='add the current channel to the whitelist or blacklist',
		guild_only=True,default_member_permissions=Permissions(manage_channels=True),
		options=[option(str,name='option',description='dad_bot commands',choices=['add','remove','list'])])
	async def slash_dad_bot(self,ctx:ApplicationContext,option:str):
		db_cfg = await self.client.db.guilds.read(ctx.guild.id,['config','dad_bot','enabled'])
		match option:
			case 'add'|'remove':
				match db_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'dad bot is currently {db_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						if option == 'add':
							await self.client.db.guilds.append(ctx.guild.id,['data','dad_bot',db_cfg],ctx.channel.id)
							res = ('added','to')
						else:
							await self.client.db.guilds.remove(ctx.guild.id,['data','dad_bot',db_cfg],ctx.channel.id)
							res = ('removed','from')
						await ctx.response.send_message(f'successfully {res[0]} {ctx.channel.mention} {res[1]} the {db_cfg}.',ephemeral=await self.client.hide(ctx))
					case _: raise
			case 'list':
				match db_cfg:
					case 'enabled'|'disabled':
						await ctx.response.send_message(f'dad bot is currently {db_cfg} for all channels. use /config to switch to a whitelist or blacklist.',ephemeral=await self.client.hide(ctx))
					case 'whitelist'|'blacklist':
						await ctx.response.send_message(embed=Embed(title=db_cfg,description='\n'.join([str(i) for i in await self.client.db.guilds.read(ctx.guild.id,['data','dad_bot',db_cfg])])),ephemeral=await self.client.hide(ctx))
					case _: raise
			case _: raise

	@slash_command(
		name='custom_auto_response',
		description='add or remove custom auto responses',
		guild_only=True,default_member_permissions=Permissions(manage_messages=True),
		options=[
			option(str,name='action',description='add, remove, or list custom auto responses',choices=['add','remove','list']),
			option(str,name='method',description='when the auto response is triggered',required=False,default='message is exactly trigger (case insensitive)',choices=list(c_au_choices.keys())),
			option(bool,name='regex',description='match with regex. useless with `contains`',required=False,default=False),
			option(Member,name='user',description='limit response to specific user',required=False,default=None),
			option(bool,name='nsfw',description='only respond in nsfw channels',required=False,default=None)])
	async def slash_custom_auto_response(self,ctx:ApplicationContext,action:str,method:str,regex:bool,user:Member,nsfw:bool) -> None:
		custom_au = await self.client.db.guilds.read(ctx.guild.id,['data','auto_responses','custom'])
		au_length = sum([len(i) for i in custom_au.values()])
		match action:
			case 'add':
				if au_length >= 50:
					await ctx.response.send_message('a single server can\'t have more than 25 custom auto responses!',ephemeral=await self.client.hide(ctx))
					return
				await ctx.response.send_modal(
					auto_response_modal(self.client,ctx.guild.id,
						'add an auto response',[
							InputText(label='trigger message',min_length=1,max_length=100,style=InputTextStyle.short),
							InputText(label='response',min_length=1,max_length=500,style=InputTextStyle.long)],
						c_au_choices.get(method,'error'),user,regex,nsfw))
			case 'remove':
				if au_length == 0:
					await ctx.response.send_message('there are no custom auto responses in this server!',ephemeral=await self.client.hide(ctx))
					return
				await ctx.response.send_modal(
					auto_response_modal(self.client,ctx.guild.id,
						'remove an auto response',[
							InputText(label='trigger message',min_length=1,max_length=100,style=InputTextStyle.short)],c_au_choices.get(method,'error')))
			case 'list':
				embed = Embed(title='custom auto responses',color=await self.client.embed_color(ctx))
				if au_length == 0: embed.description = 'no custom auto responses have been set'
				for i in ['contains','exact','exact-cs']:
					for trigger,data in custom_au.get(i,{}).items():
						value = [f'response:\n{data.get("response","no response")}']
						if data.get("regex",False):
							value.insert(0,f'regex match')
						if (user_id:=data.get("user",None)) is not None:
							value.insert(0,f'limited to user: {ctx.guild.get_member(user_id) or await ctx.guild.fetch_member(user_id)}')
						value.insert(0,f'response method: {i}')
						embed.add_field(name=trigger,value='\n'.join(value),inline=False)
				await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))
			case _: raise