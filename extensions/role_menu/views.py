
from discord.ui import View,Button,button,InputText,Item
from discord import Interaction,Embed,SelectOption
from .selects import role_menu_select
from .shared import role_inputs
from .modals import role_menu_modal
from discord.errors import Forbidden
from main import client_cls
from asyncio import Event

class role_menu_published_view(View):
	def __init__(self,client:client_cls=None,options:list[SelectOption]=None,placeholder:str=None,preview:bool=False) -> None:
		self.client = client
		super().__init__(timeout=None)
		self.add_item(role_menu_select(client,options,placeholder,preview))
	
	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		if interaction.response.is_done(): await interaction.followup.send(error,ephemeral=True)
		else: await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)

class role_menu_view(View):
	def __init__(self,*,client:client_cls,embed:Embed,current_data:dict,edit:bool) -> None:
		super().__init__()
		self.clear_items()
		self.client = client
		self.embed = embed
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
		modal = role_menu_modal(self.embed,self,[
			InputText(label='option name (case sensitive)',placeholder='server-updates',max_length=100)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		response = modal.response[0]
		if response in self.data['options']:
			self.data['options'].pop(response)

	@button(label='set placeholder',style=1)
	async def button_set_placeholder(self,button:Button,interaction:Interaction) -> None:
		self.previewed = False
		modal = role_menu_modal(self.embed,self,[
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
			self.add_item(role_menu_select(self.client,[SelectOption(value=r,label=l,description=d,emoji=e) for r,l,d,e in [list(i.values()) for i in self.data['options'].values()]],self.data['placeholder'],True))
			self.add_item(self.button_back)
			self.add_item(self.button_publish)
			await interaction.response.edit_message(embed=self.embed,view=self)
			self.previewed = True
		else:
			msg = await interaction.channel.send(view=role_menu_published_view(self.client,[SelectOption(value=r,label=l,description=d,emoji=e) for r,l,d,e in [list(i.values()) for i in self.data['options'].values()]],self.data['placeholder']))
			await self.client.db.role_menu.new(msg.id)
			await self.client.db.role_menu.write(msg.id,['placeholder'],self.data['placeholder'])
			await self.client.db.role_menu.write(msg.id,['options'],self.data['options'])
			if self.edit:
				await (await interaction.channel.fetch_message(self.edit)).delete()
				await self.client.db.role_menu.delete(self.edit)
			self.embed.title = 'success!'
			self.embed.description = 'you may now dismiss this message'
			self.clear_items()
			await interaction.response.edit_message(embed=self.embed,view=self)
	