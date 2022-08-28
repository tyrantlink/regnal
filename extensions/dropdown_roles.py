from discord import Interaction,Embed,ApplicationContext,Role,SelectOption,Message
from discord.commands import slash_command,Option as option,message_command
from discord.ui import View,Button,button,Modal,InputText,Item,Select
from discord.ext.commands import Cog
from discord.errors import Forbidden
from utils.tyrantlib import perm
from main import client_cls
from asyncio import Event
from os import urandom

role_inputs = {}

class input_text(Modal):
	def __init__(self,embed:Embed,view:View,inputs=[InputText]) -> None:
		self.embed = embed
		self.view = view
		super().__init__('set placeholder')
		for i in inputs: self.add_item(i)

	async def callback(self,interaction:Interaction) -> None:
		self.response = [i.value for i in self.children]
		
		await interaction.response.edit_message(embed=self.embed,view=self.view)
		self.stop()

class menu(Select):
	def __init__(self,client:client_cls,options:list[SelectOption],placeholder:str,preview:bool=False) -> None:
		self.client = client
		self.preview = preview
		if options is None: options = range(25)
		super().__init__(placeholder=placeholder,min_values=0,max_values=len(options),options=options,custom_id='test')

	async def callback(self,interaction:Interaction) -> None:
		if self.preview: return
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

class fview(View):
	def __init__(self,client:client_cls=None,options:list[SelectOption]=None,placeholder:str=None,preview:bool=False) -> None:
		self.client = client
		super().__init__(timeout=None)
		self.add_item(menu(client,options,placeholder,preview))
	
	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await interaction.followup.send_message(error,ephemeral=True)
		await self.client.log.error(error)

class view(View):
	def __init__(self,*,client:client_cls,embed:Embed,embed_color:int,current_data:dict,edit:bool) -> None:
		super().__init__()
		self.clear_items()
		self.client = client
		self.embed = embed
		self.embed_color = embed_color
		self.data = current_data
		self.previewed = False
		self.edit = edit
		self.add_item(self.button_set_placeholder)
		if not len(self.data['options']) >= 25: self.add_item(self.button_add_role)
		if len(self.data['options']) > 0      : self.add_item(self.button_remove_role)
		if not len(self.data['options']) == 0 : self.add_item(self.button_publish)
		

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		if interaction.response.is_done(): await interaction.followup.send(error,ephemeral=True)
		else: await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)
	
	async def main_menu_button(self,interaction:Interaction,title:str,description:str=None) -> None:
		self.embed.title = title
		self.embed.description = description
		self.clear_items()
		self.add_item(self.button_back)
		await interaction.response.edit_message(embed=self.embed,view=self)

	async def base_back(self,button:Button,interaction:Interaction):
		self.embed.title = 'create a role menu'
		self.embed.description = 'please select an option'
		self.clear_items()
		self.add_item(self.button_set_placeholder)
		if not len(self.data['options']) >= 25: self.add_item(self.button_add_role)
		if len(self.data['options']) > 0      : self.add_item(self.button_remove_role)
		if not len(self.data['options']) == 0 : self.add_item(self.button_publish)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(label='<',style=2)
	async def button_back(self,button:Button,interaction:Interaction) -> None:
		try: role_inputs.pop(interaction.user.id)
		except KeyError: pass
		await self.base_back(button,interaction)

	@button(label='add role',style=1)
	async def button_add_role(self,button:Button,interaction:Interaction) -> None:
		try: role_inputs.pop(interaction.user.id)
		except KeyError: pass
		self.previewed = False
		await self.main_menu_button(interaction,f'add a role',f'please use /add_role_to_menu to add a role.\n\nclick the back button once the role has been added.')
		role_inputs[interaction.user.id] = {'event':Event(),'response':{}}
		await role_inputs[interaction.user.id]['event'].wait()
		response = role_inputs.pop(interaction.user.id)['response']
		err = ''
		if response['label'] in self.data['options']: err += 'role label already in options\n'
		if response['role'].id in self.data['options'].values(): err += 'role already in options\n'
		try:
			await interaction.guild.me.add_roles(response['role'],reason='checking if /reg/nal can add role')
			await interaction.guild.me.remove_roles(response['role'],reason='checking if /reg/nal can add role')
		except Forbidden: err += '/reg/nal does not have permission to add this role\n'
		if err:
			await interaction.followup.send(f'Error:\n{err}',ephemeral=True)
			return
		self.data['options'][response['label']] = {'role':response['role'].id,'label':response['label'],'description':response['description'],'emoji':response['emoji']}
		await interaction.followup.send(f'successfully added role {response["role"].mention}\n\ndismiss this message and return to the role menu command',ephemeral=True)
	
	@button(label='remove role',style=1)
	async def button_remove_role(self,button:Button,interaction:Interaction) -> None:
		self.previewed = False
		modal = input_text(self.embed,self,[
			InputText(label='option name (case sensitive)',placeholder='server-updates',max_length=100)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		response = modal.response[0]
		if response in self.data['options']:
			self.data['options'].pop(response)

	@button(label='set placeholder',style=1)
	async def button_set_placeholder(self,button:Button,interaction:Interaction) -> None:
		self.previewed = False
		modal = input_text(self.embed,self,[
			InputText(label='set placeholder',placeholder=self.data['placeholder'],max_length=150)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		self.data['placeholder'] = modal.response[0]

	@button(label='publish',style=1)
	async def button_publish(self,button:Button,interaction:Interaction) -> None:
		if len(self.data['options']) == 0:
			await self.base_back(button,interaction)
			return
		if not self.previewed:
			self.embed.title = 'preview'
			self.embed.description = '*will not add roles until published'
			self.clear_items()
			self.add_item(menu(self.client,[SelectOption(value=r,label=l,description=d,emoji=e) for r,l,d,e in [list(i.values()) for i in self.data['options'].values()]],self.data['placeholder'],True))
			self.add_item(self.button_back)
			self.add_item(self.button_publish)
			await interaction.response.edit_message(embed=self.embed,view=self)
			self.previewed = True
		else:
			msg = await interaction.channel.send(view=fview(self.client,[SelectOption(value=r,label=l,description=d,emoji=e) for r,l,d,e in [list(i.values()) for i in self.data['options'].values()]],self.data['placeholder']))
			await self.client.db.dd_roles.new(msg.id)
			await self.client.db.dd_roles.write(msg.id,['placeholder'],self.data['placeholder'])
			await self.client.db.dd_roles.write(msg.id,['options'],self.data['options'])
			if self.edit:
				await (await interaction.channel.fetch_message(self.edit)).delete()
				await self.client.db.dd_roles.delete(self.edit)
			self.embed.title = 'success!'
			self.embed.description = 'you may now dismiss this message'
			self.clear_items()
			await interaction.response.edit_message(embed=self.embed,view=self)

	
class role_menu_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

	@Cog.listener()
	async def on_ready(self) -> None:
		self.client.add_view(fview(self.client))

	async def open_role_menu(self,ctx:ApplicationContext,message_id:str) -> None:
		if message_id:
			current_data = await self.client.db.dd_roles.read(int(message_id))
			if not current_data:
				await ctx.followup.send(f'`[{message_id}]` not found in role menu database',ephemeral=True)
				return
			desc = 'you are editing an existing role menu. after you are finished it will be reposted. the original message will be deleted when you are finished.'
		else:
			desc = 'please choose an option.'
			current_data = {'placeholder':'choose some roles','options':{}}
		embed_color = await self.client.embed_color(ctx)
		embed = Embed(title='create a role menu',description=desc,color=embed_color)
		await ctx.response.send_message(embed=embed,view=view(
			client=self.client,
			embed=embed,
			embed_color=embed_color,
			current_data=current_data,
			edit=message_id),
			ephemeral=True)

	@slash_command(
		name='role_menu',
		description='create a role menu',
		options=[
			option(str,name='message_id',description='edit existing role menu. menu wil be recreated',required=False,default=None)])
	@perm('manage_roles')
	async def slash_role_menu(self,ctx:ApplicationContext,message_id:str) -> None:
		await self.open_role_menu(ctx,message_id)

	@message_command(
		name='edit role menu')
	@perm('manage_roles')
	async def message_edit_role_menu(self,ctx:ApplicationContext,message:Message) -> None:
		await self.open_role_menu(ctx,message.id)
	
	@slash_command(
		name='add_role_to_menu',
		description='/role_menu must be used first',
		options=[
			option(Role,name='role',description='role'),
			option(str,name='name',description='role label'),
			option(str,name='description',description='role description',required=False),
			option(str,name='emoji',description='role emoji',required=False)])
	@perm('manage_roles')
	async def slash_add_role_to_menu(self,ctx:ApplicationContext,role:Role,label:str,description:str,emoji:str) -> None:
		if role_inputs.get(ctx.user.id) is None:
			await ctx.response.send_message(f'unable to find role menu, are you on the add role page?',ephemeral=True)
			return
		role_inputs[ctx.user.id]['response'] = {
			'role':role,
			'label':label,
			'description':description,
			'emoji':emoji}
		role_inputs[ctx.user.id]['event'].set()
		await ctx.response.send_message(f'validating role... dismiss this message',ephemeral=True)
	

def setup(client:client_cls) -> None: client.add_cog(role_menu_cog(client))