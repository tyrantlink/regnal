from discord.ui import button,InputText,user_select,channel_select,role_select,Select
from ..models import ConfigCategory,ConfigSubcategory,ConfigOption,OptionType
from discord import User,Member,Embed,Button,ButtonStyle,Interaction,Role
from .suboption_views.configure_channels import ConfigChannelsView
from ..errors import ConfigValidationError,ConfigValidationWarning
from utils.pycord_classes import SubView,MasterView,CustomModal
from utils.db.documents.ext.enums import TWBFMode
from discord.abc import GuildChannel
from re import match,IGNORECASE
from typing import Any


class ConfigOptionView(SubView):
	def __init__(self,
							master:'MasterView',
							config_category:ConfigCategory,
							config_subcategory:ConfigSubcategory,
							option:ConfigOption,
							user:User|Member,
	**kwargs) -> None:
		super().__init__(master,**kwargs)
		self.config_category = config_category
		self.config_subcategory = config_subcategory
		self.option = option
		self.user = user

	async def __ainit__(self) -> None:
		match self.config_category.name:
			case 'user': self.object_doc = await self.client.db.user(self.user.id)
			case 'guild': self.object_doc = await self.client.db.guild(self.user.guild.id)
			case _: raise ValueError('improper config category name')
		await self.handle_option()
		await self.generate_embed()

	def current_value(self) -> Any:
		return getattr(getattr(self.object_doc.config,self.config_subcategory.name),self.option.name)

	def current_value_printable(self) -> str:
		value = self.current_value()
		if value not in {'None',None}:
			match self.option.type:
				case OptionType.CHANNEL: return f'<#{value}>'
				case OptionType.ROLE: return f'<@&{value}>'
				case OptionType.USER: return f'<@{value}>'
		return str(value)

	async def give_warning(self,interaction:Interaction,warning:str|None) -> None:
		if warning is None: return
		await interaction.followup.send(Embed(
			title='warning!',color=0xffff69,
			description=warning),ephemeral=True)

	async def generate_embed(self) -> None:
		embed_color = int((await self.client.db.guild(self.user.guild.id)).config.general.embed_color,16)
		self.master.embed_color = embed_color
		self.embed = Embed(
			title=f'{self.option.name}',color=self.master.embed_color)
		if self.option.description:
			self.embed.description = self.client.helpers.handle_cmd_ref(self.option.description)
		match self.config_category.name:
			case 'user':
				self.embed.set_author(
					name=self.user.display_name,
					icon_url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
			case 'guild':
				self.embed.set_author(
					name=self.user.guild.name,
					icon_url=self.user.guild.icon.url if self.user.guild.icon else self.user.guild.me.display_avatar.url)
			case 'dev': self.embed.set_author(name=self.client.user.display_name,icon_url=self.client.user.avatar.url)
			case _: raise ValueError('improper config category name')
		self.embed.add_field(name='current value',value=self.current_value_printable(),inline=False)
		self.embed.set_footer(text=f'config.{self.config_category.name}.{self.config_subcategory.name}.{self.option.name}')

	async def handle_option(self) -> None:
		self.clear_items()
		self.add_item(self.back_button)
		self.add_item(self.button_reset)
		match self.option.type:
			case OptionType.BOOL: await self.handle_bool()
			case OptionType.TWBF: await self.handle_twbf()
			case OptionType.STRING: await self.handle_string()
			case OptionType.INT: await self.handle_int()
			case OptionType.FLOAT: await self.handle_float()
			case OptionType.CHANNEL: await self.handle_channel()
			case OptionType.ROLE: await self.handle_role()
			case OptionType.USER: await self.handle_user()
			case _: raise ValueError('improper option type')

	async def handle_bool(self) -> None:
		self.add_item(self.button_true)
		self.add_item(self.button_false)

		self.get_item('button_true').style = ButtonStyle.green if self.current_value() else ButtonStyle.red
		self.get_item('button_false').style = ButtonStyle.green if not self.current_value() else ButtonStyle.red

	async def handle_twbf(self) -> None:
		self.add_item(self.button_true)
		self.add_item(self.button_whitelist)
		self.add_item(self.button_blacklist)
		self.add_item(self.button_false)

		self.get_item('button_true').style = ButtonStyle.blurple
		self.get_item('button_whitelist').style = ButtonStyle.blurple
		self.get_item('button_blacklist').style = ButtonStyle.blurple
		self.get_item('button_false').style = ButtonStyle.blurple

		match self.current_value():
			case TWBFMode.true: self.get_item('button_true').style = ButtonStyle.green
			case TWBFMode.whitelist: self.get_item('button_whitelist').style = ButtonStyle.green
			case TWBFMode.blacklist: self.get_item('button_blacklist').style = ButtonStyle.green
			case TWBFMode.false: self.get_item('button_false').style = ButtonStyle.green
			case _: raise ValueError('improper twbf mode')

		if self.current_value() in {TWBFMode.whitelist,TWBFMode.blacklist}:
			self.add_item(self.button_configure_channels)
			self.get_item('button_configure_channels').label = f'configure {self.current_value().name}'

	async def handle_string(self) -> None:
		self.add_item(self.button_set) #! FINISH THIS (select for options)

	async def handle_int(self) -> None:
		self.add_item(self.button_set)

	async def handle_float(self) -> None:
		self.add_item(self.button_set)

	async def handle_channel(self) -> None:
		self.add_item(self.select_channel)
		if self.option.attrs.max_value: self.get_item('select_channel').max_values = self.option.attrs.max_value
		if self.option.attrs.min_value: self.get_item('select_channel').min_values = self.option.attrs.min_value

	async def handle_role(self) -> None:
		self.add_item(self.select_role)
		if self.option.attrs.max_value: self.get_item('select_role').max_values = self.option.attrs.max_value
		if self.option.attrs.min_value: self.get_item('select_role').min_values = self.option.attrs.min_value

	async def handle_user(self) -> None:
		self.add_item(self.select_user)
		if self.option.attrs.max_value: self.get_item('select_user').max_values = self.option.attrs.max_value
		if self.option.attrs.min_value: self.get_item('select_user').min_values = self.option.attrs.min_value

	async def validate_bool(self,value:bool) -> bool:
		return value

	async def validate_twbf(self,value:TWBFMode) -> TWBFMode:
		return value

	async def validate_string(self,value:str) -> str:
		if self.option.attrs.regex and not match(self.option.attrs.regex,value,IGNORECASE): raise ConfigValidationError(f'failed to match regex `{self.option.attrs.regex}`')
		return value

	async def validate_int(self,value:str) -> int:
		try: value = int(value)
		except ValueError: raise ConfigValidationError('value must be an int')
		if self.option.attrs.max_value and value > self.option.attrs.max_value: raise ConfigValidationError(f'value cannot be greater than `{self.option.attrs.max_value}`')
		if self.option.attrs.min_value and value < self.option.attrs.min_value: raise ConfigValidationError(f'value cannot be less than `{self.option.attrs.min_value}`')
		return value

	async def validate_float(self,value:str) -> float:
		try: value = float(value)
		except ValueError: raise ConfigValidationError('value must be a float')
		if self.option.attrs.max_value and value > self.option.attrs.max_value: raise ConfigValidationError(f'value cannot be greater than `{self.option.attrs.max_value}`')
		if self.option.attrs.min_value and value < self.option.attrs.min_value: raise ConfigValidationError(f'value cannot be less than `{self.option.attrs.min_value}`')
		return value

	async def validate_channel(self,value:GuildChannel) -> GuildChannel:
		return value

	async def validate_role(self,value:Role) -> Role:
		return value

	async def validate_user(self,value:Member) -> User|Member:
		return value

	async def write_config(self,value:Any) -> str|None:
		match self.option.type:
			case OptionType.BOOL: value = await self.validate_bool(value)
			case OptionType.TWBF: value = await self.validate_twbf(value)
			case OptionType.STRING: value = await self.validate_string(value)
			case OptionType.INT: value = await self.validate_int(value)
			case OptionType.FLOAT: value = await self.validate_float(value)
			case OptionType.CHANNEL: value = await self.validate_channel(value)
			case OptionType.ROLE: value = await self.validate_role(value)
			case OptionType.USER: value = await self.validate_user(value)
			case _: raise ValueError('improper option type')
		warning = None
		if self.option.attrs.validation is not None:
			value,warning = await self.option.attrs.validation(self.client,self.option,value,self.user)

		if self.option.type in {OptionType.CHANNEL,OptionType.ROLE,OptionType.USER}: value = value.id if value else None

		setattr(getattr(self.object_doc.config,self.config_subcategory.name),self.option.name,value)
		await self.object_doc.save_changes()
		match self.config_category.name:
			case 'user': print_id = self.user.id
			case 'guild': print_id = self.user.guild.id
			case 'dev': print_id = self.client.user.id
			case _: raise ValueError('improper config category name')
		self.client.log.info(f'{self.user.name} set {self.config_category.name}[{print_id}].{self.config_subcategory.name}.{self.option.name} to {value}',
													user=self.user.id,guild=getattr(getattr(self.user,'guild',None),'id',None),
													option=f'{self.config_category.name}.{self.config_subcategory.name}.{self.option.name}',value=value)
		await self.generate_embed()
		await self.handle_option()
		return warning

	@button(
		label='reset to default',row=3,
		style=ButtonStyle.red,
		custom_id='button_reset')
	async def button_reset(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(self.option.default)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)

	@button(
		label='true',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_true')
	async def button_true(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(True if self.option.type == OptionType.BOOL else TWBFMode.true)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)

	@button(
		label='false',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_false')
	async def button_false(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(False if self.option.type == OptionType.BOOL else TWBFMode.false)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)

	@button(
		label='whitelist',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_whitelist')
	async def button_whitelist(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(TWBFMode.whitelist)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)

	@button(
		label='blacklist',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_blacklist')
	async def button_blacklist(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(TWBFMode.blacklist)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)

	@button(
		label='configure channels',row=3,
		style=ButtonStyle.blurple,
		custom_id='button_configure_channels')
	async def button_configure_channels(self,button:Button,interaction:Interaction) -> None:
		view = self.master.create_subview(ConfigChannelsView,self.config_category,self.config_subcategory,self.option,self.user)
		await view.__ainit__()
		await interaction.response.edit_message(view=view,embed=view.embed)

	@button(
		label='set',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_set')
	async def button_set(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(
			f'set {self.option.name}',
			[InputText(
				label=self.option.name,
				placeholder=self.option.attrs.placeholder,
				max_length=self.option.attrs.max_length,
				min_length=self.option.attrs.min_length,
				custom_id='input_set')])

		await interaction.response.send_modal(modal)

		await modal.wait()
		warning = await self.write_config(modal.children[0].value)
		await modal.interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)
	
	@channel_select(
		placeholder='select a channel',
		custom_id='select_channel',row=1,min_values=0)
	async def select_channel(self,select:Select,interaction:Interaction) -> None:
		warning = await self.write_config(
			select.values if len(select.values) > 1 else select.values[0] if select.values else None)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)
	
	@role_select(
		placeholder='select a role',
		custom_id='select_role',row=1,min_values=0)
	async def select_role(self,select:Select,interaction:Interaction) -> None:
		warning = await self.write_config(
			select.values if len(select.values) > 1 else select.values[0] if select.values else None)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)
	
	@user_select(
		placeholder='select a user',
		custom_id='select_user',row=1,min_values=0)
	async def select_user(self,select:Select,interaction:Interaction) -> None:
		warning = await self.write_config(
			select.values if len(select.values) > 1 else select.values[0] if select.values else None)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)
