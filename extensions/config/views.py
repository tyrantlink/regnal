from discord.ui import View,Button,button,Item,channel_select,Select,string_select,role_select,user_select,InputText
from discord.enums import ComponentType
from discord import Interaction,Embed,Member,User,SelectOption
from utils.tyrantlib import dev_only
from functools import partial
from .shared import config
from .modals import config_modal
from main import client_cls
from os import urandom


class config_view(View):
	def __init__(self,client:client_cls,embed:Embed,user:User|Member,current_config:dict) -> None:
		tmp,self.__view_children_items__ = self.__view_children_items__,[]
		super().__init__()
		self.__view_children_items__ = tmp
		self._item_init()
		self.client         = client
		self.embed          = embed
		self.user           = user
		self.current_config = current_config
		self.category = 'main'
		self.missing = urandom(8)

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await self.client.on_error(interaction,error)

	def add_items(self,*items:Item) -> None:
		for item in items: self.add_item(item)

	def _item_init(self):
		for func in self.__view_children_items__:
			item: Item = func.__discord_ui_model_type__(**func.__discord_ui_model_kwargs__)
			item.callback = partial(func,self,item)
			item._view = self
			setattr(self,func.__name__,item)

	def reload(self) -> None:
		self.category = self.category
		self.selected_option = self.selected_option
		item = self.get_item('option_select')
		if item is not None: item.placeholder = self.selected_option
	
	def set_category_select_options(self,mode='main') -> None:
		match mode:
			case 'main':
				options = [SelectOption(label='user',description='user specific config')]
				if isinstance(self.user,Member) and self.user.guild_permissions.manage_guild:
					options.append(SelectOption(label='guild',description='guild config menu'))
				if self.user.id == self.client.owner_id:
					options.append(SelectOption(label='dev',description='dev options'))

				if len(options) == 1:
					self.category = 'user'
					self.remove_item(self.back_button)
					return True
			case 'guild':
				options = [SelectOption(label='general',description='general options')]
				if self.user.guild_permissions.view_audit_log:
					options.append(SelectOption(label='logging',description='logging config'))
				if self.user.guild_permissions.manage_channels:
					options.append(SelectOption(label='qotd',description='qotd config'))
					options.append(SelectOption(label='talking_stick',description='talking stick config'))
				if self.user.guild_permissions.manage_messages:
					options.append(SelectOption(label='auto_responses',description='auto response config'))
					options.append(SelectOption(label='dad_bot',description='dad bot config'))

		self.get_item('category_select').options = options
		
	async def modify_config(self,value) -> None:
		match self.category:
			case 'user':
				await self.client.db.users.write(self.user.id,['config',self.selected_option],value)
				self.current_config['user'][self.selected_option] = value
			case 'general'|'logging'|'qotd'|'talking_stick'|'auto_responses'|'dad_bot': # guild submenus
				await self.client.db.guilds.write(self.user.guild.id,['config',self.category,self.selected_option],value)
				self.current_config['guild'][self.category][self.selected_option] = value
			case 'dev': 
				await self.client.db.inf.write('/reg/nal',['config',self.selected_option],value)
				self.current_config['dev'][self.selected_option] = value
			case 'main'|'guild'|_: raise
		

	def validate_modal_input(self,value:str) -> int:
		data = config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,None)
		if data is None: raise
		match self.selected_option:
			case 'embed_color': return int(value.replace('#',''),16)
			case 'max_roll':
				if not (16384 > int(value) > 2): raise
				return int(value)
			case _: raise

	@property
	def category(self) -> str:
		return self._category

	@property
	def selected_option(self) -> str:
		return self._selected_option

	@category.setter
	def category(self,value) -> None:
		self.embed.description = None
		self.embed.clear_fields()
		self.clear_items()
		self.embed.title = f'{value} config'
		match value:
			case 'main':
				self.embed.title = 'config'
				self.add_items(self.category_select)
				if self.set_category_select_options(): return
			case 'user':
				for k,v in self.current_config.get('user',{}).items(): self.embed.add_field(name=k,value=v)
				self.add_items(self.option_select,self.back_button)
				self.get_item('option_select').options = [SelectOption(label=label) for label in config.get('user',{}).keys()]
				self.get_item('option_select').placeholder = 'select an option'
			case 'guild':
				self.add_items(self.category_select,self.back_button)
				self.set_category_select_options(value)
			case 'general'|'logging'|'qotd'|'talking_stick'|'auto_responses'|'dad_bot': # guild submenus
				c = config.get('guild',{}).get(value,{})
				for k,v in self.current_config.get('guild',{}).get(value,{}).items():
					if v is not None: 
						match c[k]['type']:
							case 'channel': v = f'<#{v}>'
							case 'user'   : v = f'<@{v}>'
							case 'role'   : v = f'<@&{v}>'
					self.embed.add_field(name=k,value=v)
				self.add_items(self.option_select,self.back_button)
				self.get_item('option_select').options = [SelectOption(label=label) for label in config.get('guild',{}).get(value,{}).keys()]
				self.get_item('option_select').placeholder = 'select an option'
			case 'dev':
				for k,v in self.current_config.get('dev',{}).items(): self.embed.add_field(name=k,value=v)
				self.add_items(self.option_select,self.back_button)
				self.get_item('option_select').options = [SelectOption(label=label) for label in config.get('dev',{}).keys()]
				self.get_item('option_select').placeholder = 'select an option'
			case _: raise
		self._category = value

	@selected_option.setter
	def selected_option(self,value) -> None:
		for i in self.children:
			if i.type != 3 or i.custom_id == 'back_button': continue
			self.remove_item(i)

		data = config.get(self.category,config.get('guild',{}).get(self.category,{})).get(value,None)
		# print(t)
		# data = t
		# print(data)
		if data is None: raise
		self.embed.description = data.get('description',None)
		opt_type = data.get('type',None)

		match opt_type:
			case 'bool':
				self.add_items(self.enable_button,self.disable_button,self.default_button)
			case 'ewbd':
				self.add_items(self.enable_button,self.whitelist_button,self.blacklist_button,self.disable_button,self.default_button)
			case 'modal':
				self.add_items(self.set_button,self.default_button)
			case 'channel':
				self.remove_item(self.back_button)
				self.add_items(self.channel_select,self.back_button,self.default_button)
			case 'role':
				self.remove_item(self.back_button)
				self.add_items(self.role_select,self.back_button,self.default_button)
			case None|_: raise

		self._selected_option = value#(value,opt_type)
	
	@string_select(
		custom_id='category_select',
		placeholder='please select a config category')
	async def category_select(self,select:Select,interaction:Interaction) -> None:
		self.category = select.values[0]
		await interaction.response.edit_message(embed=self.embed,view=self)

	@string_select(
		custom_id='option_select',
		placeholder='select an option')
	async def option_select(self,select:Select,interaction:Interaction) -> None:
		self.selected_option = select.values[0]
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@channel_select(
		custom_id='channel_select',
		placeholder='select a channel')
	async def channel_select(self,select:Select,interaction:Interaction) -> None:
		await self.modify_config(select.values[0].id)
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@role_select(
		custom_id='role_select',
		placeholder='select a role')
	async def role_select(self,select:Select,interaction:Interaction) -> None:
		await self.modify_config(select.values[0].id)
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)
	
	# @user_select(
	# 	custom_id='user_select',
	# 	placeholder='select a role')
	# async def user_select(self,select:Select,interaction:Interaction) -> None:
	# 	self.selected_option = select.values[0]
	# 	await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='<',style=2,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		match self.category:
			case 'user'|'guild'|'dev': self.category = 'main'
			case 'general'|'logging'|'qotd'|'talking_stick'|'auto_responses'|'dad_bot':
				self.category = 'guild'
			case 'main': self.remove_item(self.back_button)
			case _: raise
		await interaction.response.edit_message(embed=self.embed,view=self)
	
	@button(
		label='enable',style=3,
		custom_id='enable_button')
	async def enable_button(self,button:Button,interaction:Interaction) -> None:
		match config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,{}).get('type',self.missing):
			case 'ewbd': await self.modify_config('enabled')
			case 'bool': await self.modify_config(True)
			case _     : raise
		self.reload()
		
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='whitelist',style=1,
		custom_id='whitelist_button')
	async def whitelist_button(self,button:Button,interaction:Interaction) -> None:
		await self.modify_config('whitelist')
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='blacklist',style=1,
		custom_id='blacklist_button')
	async def blacklist_button(self,button:Button,interaction:Interaction) -> None:
		await self.modify_config('blacklist')
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='disable',style=4,
		custom_id='disable_button')
	async def disable_button(self,button:Button,interaction:Interaction) -> None:
		match config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,{}).get('type',self.missing):
			case 'ewbd': await self.modify_config('disabled')
			case 'bool': await self.modify_config(False)
			case _     : raise
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='set',style=1,
		custom_id='set_button')
	async def set_button(self,button:Button,interaction:Interaction) -> None:
		
		modal = config_modal(self,f'set {self.selected_option}',
			[InputText(label=self.selected_option,
				max_length=config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,{}).get('max_length',None))])
		
		await interaction.response.send_modal(modal)
		await modal.wait()
		await self.modify_config(self.validate_modal_input(modal.children[0].value))
		self.reload()
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='reset to default',row=2,style=4,
		custom_id='default_button')
	async def default_button(self,button:Button,interaction:Interaction) -> None:
		value = config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,{}).get('default',self.missing)
		await self.modify_config(value)
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)


	
