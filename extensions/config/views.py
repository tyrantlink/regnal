from discord.ui import View,Button,button,Item,channel_select,Select,string_select,role_select,user_select,InputText
from discord import Interaction,Embed,Member,User,SelectOption,InputTextStyle
from .modals import config_modal
from functools import partial
from main import client_cls
from .shared import config
from os import urandom

class configure_list_view(View):
	def __init__(self,option_type:str,original_view:View,client:client_cls,embed:Embed) -> None:
		tmp,self.__view_children_items__ = self.__view_children_items__,[]
		super().__init__(timeout=0)
		self.__view_children_items__ = tmp
		self._item_init()
		self.option_type    = option_type
		self.original_view  = original_view
		self.client         = client
		self.embed          = embed
		self.add_items(self.channel_select,self.back_button,self.add_button,self.remove_button)

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

	async def reload(self,guild_id) -> None:
		self.embed.description = f'currently {self.option_type[1]}ed:\n'+('\n'.join([f'<#{i}>' for i in await self.client.db.guilds.read(guild_id,['data',self.option_type[0],self.option_type[1]])]) or 'None')

	@channel_select(
		custom_id='channel_select',row=0,
		placeholder='select some channels',max_values=25)
	async def channel_select(self,select:Select,interaction:Interaction) -> None:
		self.channels_selected = select.values
		await interaction.response.edit_message(embed=self.embed,view=self)
	
	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.edit_message(embed=self.original_view.embed,view=self.original_view)

	@button(
		label='add',style=3,row=1,
		custom_id='add_button')
	async def add_button(self,button:Button,interaction:Interaction) -> None:
		current:list = await self.client.db.guilds.read(interaction.guild.id,['data',self.option_type[0],self.option_type[1]])
		for i in self.channels_selected:
			if i.id not in current: current.append(i.id)
		await self.client.db.guilds.write(interaction.guild.id,['data',self.option_type[0],self.option_type[1]],current)
		await self.reload(interaction.guild.id)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=1,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		current:list = await self.client.db.guilds.read(interaction.guild.id,['data',self.option_type[0],self.option_type[1]])
		for i in self.channels_selected:
			if i.id in current: current.remove(i.id)
		await self.client.db.guilds.write(interaction.guild.id,['data',self.option_type[0],self.option_type[1]],current)
		await self.reload(interaction.guild.id)
		await interaction.response.edit_message(embed=self.embed,view=self)

class custom_au_view(View):
	def __init__(self,original_view:View,client:client_cls,embed:Embed,custom_au:dict) -> None:
		tmp,self.__view_children_items__ = self.__view_children_items__,[]
		super().__init__(timeout=0)
		self.__view_children_items__ = tmp
		self._item_init()
		self.original_view = original_view
		self.client        = client
		self.embed         = embed
		self.custom_au     = custom_au
		self.page          = 'main'
		self.selected_au   = None
		self.remove_confirmed = False
		self.new_au = None
		self.add_items(self.page_select,self.back_button)
	
	@property
	def default_new_au(self):
		return {
			'method':None,
			'trigger':None,
			'response':None,
			'user':None,
			'regex':False,
			'nsfw':False}

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
	
	def au_reload(self,guild_id:int) -> None:
		for i in self.client.flags:
			if i[0] != 'RELOAD_AU': continue
			if guild_id not in i:
				self.client.flags.remove(i)
				self.client.flags.append((*i,guild_id))
		else:
			self.client.flags.append(('RELOAD_AU',guild_id))

	def reload(self) -> None:
		self.selected_au = None
		self.remove_confirmed = False
		self.embed.description = None
		self.embed.clear_fields()
		self.clear_items()
		match self.page:
			case 'main':
				self.add_items(self.page_select,self.back_button)
			case 'contains'|'exact'|'exact-cs':
				self.embed.add_field(name='method',value=self.page)
				self.add_items(self.custom_au_select,self.back_button,self.new_button)
				for child in self.children:
					if child.custom_id != 'new_button': continue
					if len(self.custom_au.get(self.page,{}).keys()) >= 25: child.disabled = True
					else: child.disabled = False
				self.update_select()
			case 'new':
				self.add_items(self.limit_user_select,self.back_button,self.set_button,self.regex_button,self.nsfw_button,self.save_button)
			case _: raise

	def update_select(self):
		for child in self.children:
			if child.custom_id != 'custom_au_select': continue
			if (options:=[SelectOption(label=k) for k in [i for i in self.custom_au.get(self.page,{}).keys()]]):
				child.options = options
				child.placeholder = 'select an auto response'
				child.disabled = False
			else:
				child.options = [SelectOption(label='None')]
				child.placeholder = 'there are no custom auto responses'
				child.disabled = True
			break

	def embed_au(self,au:dict):
		self.embed.clear_fields()
		self.embed.add_field(name='method',value=au.get('method','ERROR'))
		self.embed.add_field(name='match with regex',value=au.get('regex',False))
		self.embed.add_field(name='limited to user',value=f"<@{au.get('user',False)}>" if au.get('user',False) else False)
		self.embed.add_field(name='nsfw',value=au.get('nsfw',False))
		self.embed.add_field(name='trigger',value=au.get('trigger','ERROR'),inline=False)
		self.embed.add_field(name='response',value=au.get('response',False),inline=False)
		for child in self.children:
			match child.custom_id:
				case 'regex_button': child.style = 3 if au.get('regex',False) else 4
				case 'nsfw_button': child.style = 3 if au.get('nsfw',False) else 4
				case _: continue

	@string_select(
		custom_id='page_select',row=0,
		placeholder='select a category',
		options=[SelectOption(label=i) for i in ['contains','exact','exact-cs']])
	async def page_select(self,select:Select,interaction:Interaction) -> None:
		self.page = select.values[0]
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@string_select(
		custom_id='custom_au_select',row=0,
		placeholder='select an auto response')
	async def custom_au_select(self,select:Select,interaction:Interaction) -> None:
		self.selected_au = select.values[0]
		self.remove_confirmed = False
		self.embed.description = None
		au = self.custom_au.get(self.page,{}).get(self.selected_au,{})
		au.update({'method':self.page,'trigger':self.selected_au})
		self.embed_au(au)
		self.add_item(self.edit_button)
		if len(self.custom_au.get(self.page,{}).keys()) != 0: self.add_item(self.remove_button)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		if self.page == 'main':
			await interaction.response.edit_message(embed=self.original_view.embed,view=self.original_view)
			return
		self.page = 'main'
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='new',style=3,row=1,
		custom_id='new_button')
	async def new_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au = self.default_new_au
		self.new_au.update({'method':self.page})
		self.page = 'new'
		self.reload()
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='edit',style=1,row=1,
		custom_id='edit_button')
	async def edit_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au = self.custom_au.get(self.page,{}).get(self.selected_au)
		self.new_au.update({'method':self.page})
		self.page = 'new'
		self.reload()
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=1,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		if self.remove_confirmed:
			if self.selected_au is None: raise
			self.custom_au[self.page].pop(self.selected_au)
			await self.client.db.guilds.unset(interaction.guild.id,['data','auto_responses','custom',self.page,self.selected_au.replace('.','\.')])
			self.au_reload(interaction.guild.id)
			self.reload()
		else:
			self.embed.description = 'are you sure you want to remove this auto response?\nclick remove again to remove it.'
			self.remove_confirmed = True
		await interaction.response.edit_message(embed=self.embed,view=self)

	@user_select(
		placeholder='limit to a user',
		custom_id='limit_user_select',min_values=0)
	async def limit_user_select(self,select:Select,interaction:Interaction) -> None:
		if select.values: self.new_au.update({'user':select.values[0].id})
		else: self.new_au.update({'user':None})
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='set',style=1,row=1,
		custom_id='set_button')
	async def set_button(self,button:Button,interaction:Interaction) -> None:
		modal = config_modal(self,'add custom auto response',[
			InputText(label='trigger message',placeholder='cannot start with $ or contain a .',min_length=1,max_length=100,style=InputTextStyle.short,value=self.new_au.get('trigger')),
			InputText(label='response',min_length=1,max_length=500,style=InputTextStyle.long,value=self.new_au.get('response'))])
		
		await interaction.response.send_modal(modal)
		await modal.wait()
		if modal.children[0].value.startswith('$') or '.' in modal.children[0].value:
			embed = Embed(title='an error has occurred!',color=0xff6969)
			embed.add_field(name='error',value='auto response trigger cannot start with $ or contain a .')
			await modal.interaction.response.send_message(embed=embed,ephemeral=self.client.hide(interaction))
			return
		self.new_au.update({
			'trigger':modal.children[0].value,	
			'response':modal.children[1].value})
		self.embed_au(self.new_au)
		for child in self.children:
			if child.custom_id != 'save_button': continue
			child.disabled = False
			break
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='regex',style=4,row=1,
		custom_id='regex_button')
	async def regex_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au.update({'regex':not self.new_au.get('regex')})
		if self.new_au.get('regex'): button.style = 3
		else: button.style = 4
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='nsfw',style=4,row=1,
		custom_id='nsfw_button')
	async def nsfw_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au.update({'nsfw':not self.new_au.get('nsfw')})
		if self.new_au['nsfw']: button.style = 3
		else: button.style = 4
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='save',style=3,row=2,
		custom_id='save_button',disabled=True)
	async def save_button(self,button:Button,interaction:Interaction) -> None:
		old_page = self.new_au.pop('method')
		self.custom_au[old_page][self.new_au.pop('trigger')] = self.new_au
		await self.client.db.guilds.write(interaction.guild.id,['data','auto_responses','custom',old_page],self.custom_au.get(old_page))
		self.au_reload(interaction.guild.id)
		self.page = old_page
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

class config_view(View):
	def __init__(self,client:client_cls,embed:Embed,user:User|Member,current_config:dict) -> None:
		tmp,self.__view_children_items__ = self.__view_children_items__,[]
		super().__init__(timeout=0)
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

	async def _no_track_enabled(self) -> None:
		await self.client.db.users.write(self.user.id,['messages'],None)
		for guild in self.user.mutual_guilds:
			await self.client.db.guilds.unset(guild.id,['data','leaderboards','messages',str(self.user.id)])
			await self.client.db.guilds.unset(guild.id,['data','leaderboards','sticks',str(self.user.id)])

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
		if self.selected_option == 'no_track':
			if value: await self._no_track_enabled()
			else    : await self.client.db.users.write(self.user.id,['messages'],0)
		await self.client.log.debug(f'[CONFIG] [{self.category.upper()}] {self.user} set {self.selected_option} to {value}',config={'category':self.category,'option':self.selected_option,'set_to':value})

	def validate_modal_input(self,value:str) -> int:
		data = config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,None)
		if data is None: raise
		match self.selected_option:
			case 'embed_color': return int(value.replace('#',''),16)
			case 'max_roll':
				if not (16384 > int(value) > 2): raise
				return int(value)
			case 'cooldown':
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
				if value == 'auto_responses': self.add_item(self.custom_au_button)
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
		if data is None: raise
		self.embed.description = data.get('description',None)
		opt_type = data.get('type',None)

		match opt_type:
			case 'bool':
				self.add_items(self.enable_button,self.disable_button,self.default_button)
			case 'ewbd':
				self.add_items(self.enable_button,self.whitelist_button,self.blacklist_button,self.disable_button,self.default_button)
				if (mode:=self.current_config.get('guild',{}).get(self.category,{}).get(value,None)) in ['whitelist','blacklist']:
					self.add_item(self.configure_list_button)
					for child in self.children:
						if child.custom_id != 'configure_list_button': continue
						child.label = f'configure {mode}'
			case 'modal':
				self.add_items(self.set_button,self.default_button)
			case 'channel':
				self.remove_item(self.back_button)
				self.add_items(self.channel_select,self.back_button,self.default_button)
			case 'role':
				self.remove_item(self.back_button)
				self.add_items(self.role_select,self.back_button,self.default_button)
			case None|_: raise

		self._selected_option = value
	
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
		option = config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,{})
		modal = config_modal(self,f'set {self.selected_option}',
			[InputText(label=self.selected_option,
				max_length=option.get('max_length',None))])
		
		await interaction.response.send_modal(modal)
		await modal.wait()
		await self.modify_config(self.validate_modal_input(modal.children[0].value))
		self.reload()
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='configure',style=1,row=2,
		custom_id='configure_list_button')
	async def configure_list_button(self,button:Button,interaction:Interaction) -> None:
		mode = self.current_config.get('guild',{}).get(self.category,{}).get(self.selected_option,None)
		embed = Embed(
			title=f'configure {self.category} {mode}',
			description=f'currently {mode}ed:\n'+('\n'.join([f'<#{i}>' for i in await self.client.db.guilds.read(interaction.guild.id,['data',self.category,mode])]) or 'None'),
			color=self.embed.color)
		await interaction.response.edit_message(embed=embed,view=configure_list_view((self.category,mode),self,self.client,embed))

	@button(
		label='custom auto responses',style=1,row=1,
		custom_id='custom_au_button')
	async def custom_au_button(self,button:Button,interaction:Interaction) -> None:
		embed = Embed(
			title=f'custom auto responses',
			color=self.embed.color)
		await interaction.response.edit_message(embed=embed,view=custom_au_view(self,self.client,embed,await self.client.db.guilds.read(interaction.guild.id,['data','auto_responses','custom'])))

	@button(
		label='reset to default',row=4,style=4,
		custom_id='default_button')
	async def default_button(self,button:Button,interaction:Interaction) -> None:
		value = config.get(self.category,config.get('guild',{}).get(self.category,{})).get(self.selected_option,{}).get('default',self.missing)
		await self.modify_config(value)
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)