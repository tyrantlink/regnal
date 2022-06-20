from discord import SelectOption,Interaction,Role,Interaction,Embed,ApplicationContext
from discord.commands import SlashCommandGroup,Option as option
from discord.ui import Select,View,Item
from discord.ext.commands import Cog
from utils.tyrantlib import perm
from discord.errors import Forbidden
from main import client_cls

class dropdown(Select):
	def __init__(self,client:client_cls,options:list,placeholder:str) -> None:
		self.client = client
		if options is None: options = range(25)
		super().__init__(placeholder=placeholder,min_values=0,max_values=len(options),options=options,custom_id='test')

	async def callback(self,interaction:Interaction) -> None:
		current_roles = [role.id for role in interaction.user.roles]
		option_data = await self.client.db.dd_roles.read(interaction.message.id,['options'])
		possible_options = [option_data[i]['role'] for i in option_data]
		added_roles,removed_roles = [],[]
		for role in possible_options:
			role = interaction.guild.get_role(role)
			if str(role.id) in self.values and role.id not in current_roles:
				try: await interaction.user.add_roles(role)
				except Forbidden:
					await interaction.response.send_message('a permission error has occurred, contact a moderator.',ephemeral=True)
				added_roles.append(role.mention)
			elif str(role.id) not in self.values and role.id in current_roles:
				try: await interaction.user.remove_roles(role)
				except Forbidden:
					await interaction.response.send_message('a permission error has occurred, contact a moderator.',ephemeral=True)
				removed_roles.append(role.mention)
		res = Embed(title='successfully modified roles',color=await self.client.embed_color(interaction))
		if added_roles: res.add_field(name='added',value='\n'.join(added_roles))
		if removed_roles: res.add_field(name='removed',value='\n'.join(removed_roles))
		if added_roles or removed_roles: await interaction.response.send_message(embed=res,ephemeral=True)

class view(View):
	def __init__(self,client:client_cls=None,options:list=None,placeholder:str=None) -> None:
		self.client = client
		super().__init__(timeout=None)
		self.add_item(dropdown(client,options,placeholder))
	
	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)

class dropdown_roles_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

	@Cog.listener()
	async def on_ready(self) -> None:
		self.client.add_view(view(self.client))

	dropdown_roles = SlashCommandGroup('dropdown_roles','dropdown role commands')

	@dropdown_roles.command(
		name='create',
		description='create a dropdown role menu',
		options=[
			option(Role,name='role',description='first role'),
			option(str,name='name',description='role label'),
			option(str,name='description',description='role description',required=False),
			option(str,name='emoji',description='role emoji',required=False),
			option(str,name='placeholder',description='placeholder text when no roles are selected',default='choose some roles',required=False)])
	@perm('manage_roles')
	async def slash_dropdown_roles_create(self,ctx:ApplicationContext,role:Role,label:str,description:str,emoji:str,placeholder:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		dd_role_message = await ctx.channel.send(view=view(self.client,[SelectOption(label=label,description=description,emoji=emoji,value=str(role.id))],placeholder))
		await self.client.db.dd_roles.new(dd_role_message.id)
		await self.client.db.dd_roles.write(dd_role_message.id,['placeholder'],placeholder)
		await self.client.db.dd_roles.write(dd_role_message.id,['options',label],{'role':role.id,'label':label,'description':description,'emoji':emoji})
		await ctx.followup.send(f'successfully created dropdown menu. message_id: `{dd_role_message.id}`',ephemeral=True)

	@dropdown_roles.command(
		name='add_role',
		description='add role to existing menu. 25 max',
		options=[
			option(str,name='message_id',description='id of existing menu message'),
			option(Role,name='role',description='role'),
			option(str,name='name',description='role label'),
			option(str,name='description',description='role description',required=False),
			option(str,name='emoji',description='role emoji',required=False)])
	@perm('manage_roles')
	async def slash_dropdown_roles_add(self,ctx:ApplicationContext,message_id:str,role:Role,label:str,description:str,emoji:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		message_id = int(message_id)
		current_data = await self.client.db.dd_roles.read(message_id)
		current_message = await ctx.channel.fetch_message(message_id)
		if not current_data:
			await ctx.followup.send(f'`{message_id}` not found in database',ephemeral=True)
			return
		if not current_message:
			await ctx.followup.send('message not found on discord. was it deleted?',ephemeral=True)
			return
		if len(current_data['options']) >= 25:
			await ctx.followup.send('you cannot add more than 25 roles',ephemeral=True)
			return
		if label in current_data['options']:
			if current_data['options'][label] is not None:
				await ctx.followup.send('role label already in options',ephemeral=True)
				return
		if role.id in current_data['options'].values():
			await ctx.followup.send('role already in options',ephemeral=True)
			return
		await self.client.db.dd_roles.write(message_id,['options',label],{'role':role.id,'label':label,'description':description,'emoji':emoji})
		new_data = await self.client.db.dd_roles.read(message_id)
		await current_message.edit(view=view(self.client,[SelectOption(label=o[1]['label'],description=o[1]['description'],emoji=o[1]['emoji'],value=str(o[1]['role'])) for o in new_data['options'].items() if o[1] is not None],new_data['placeholder']))
		await ctx.followup.send(f'successfully added {label} to menu. message_id: `{message_id}`',ephemeral=True)
	
	@dropdown_roles.command(
		name='remove_role',
		description='remove role from existing menu',
		options=[
			option(str,name='message_id',description='id of existing menu message'),
			option(str,name='label',description='role label')])
	@perm('manage_roles')
	async def slash_dropdown_roles_remove(self,ctx:ApplicationContext,message_id:str,label:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		message_id = int(message_id)
		current_data = await self.client.db.dd_roles.read(message_id)
		current_message = await ctx.channel.fetch_message(message_id)
		if not current_data:
			await ctx.followup.send(f'`{message_id}` not found in database',ephemeral=True)
			return
		if not current_message:
			await ctx.followup.send('message not found on discord. was it deleted?',ephemeral=True)
			return
		if label not in current_data['options'].keys():
			await ctx.followup.send('role label not found. is it exact?',ephemeral=True)
			return
		await self.client.db.dd_roles.unset(message_id,['options',label])
		new_data = await self.client.db.dd_roles.read(message_id)
		await current_message.edit(view=view(self.client,[SelectOption(label=o[1]['label'],description=o[1]['description'],emoji=o[1]['emoji'],value=str(o[1]['role'])) for o in new_data['options'].items() if o[1] is not None],new_data['placeholder']))
		await ctx.followup.send(f'successfully removed {label} from menu. message_id: `{message_id}`',ephemeral=True)

	@dropdown_roles.command(
		name='refresh_menu',
		description='refresh existing menu',
		options=[
			option(str,name='message_id',description='id of existing menu message')])
	@perm('manage_roles')
	async def slash_dropdown_roles_refresh_menu(self,ctx:ApplicationContext,message_id:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		message_id = int(message_id)
		data = await self.client.db.dd_roles.read(message_id)
		message = await ctx.channel.fetch_message(message_id)
		if not data:
			await ctx.followup.send(f'`{message_id}` not found in database',ephemeral=True)
			return
		if not message:
			await ctx.followup.send('message not found on discord. was it deleted?',ephemeral=True)
			return
		await message.edit(view=view(self.client,[SelectOption(label=o[1]['label'],description=o[1]['description'],emoji=o[1]['emoji'],value=str(o[1]['role'])) for o in data['options'].items() if o[1] is not None],data['placeholder']))
		await ctx.followup.send(f'successfully refreshed menu. message_id: `{message_id}`',ephemeral=True)


def setup(client:client_cls) -> None: client.add_cog(dropdown_roles_cog(client))