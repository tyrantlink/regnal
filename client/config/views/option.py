from ..models import ConfigCategory,ConfigSubcategory,ConfigOption,OptionType
from utils.atomic_view import SubView,MasterView,CustomModal
from discord import User,Member,Embed,Button,ButtonStyle,Interaction,Role
from discord.ui import button,InputText
from typing import Any
from utils.db.documents.ext.enums import TWBFMode
from .helpers import handle_user_no_track,validate_qotd_channel
from re import match,IGNORECASE
from .enums import ValidOption
from discord.abc import GuildChannel
from discord.enums import ChannelType

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
	
	async def current_value(self) -> Any:
		return getattr(getattr(self.object_doc.config,self.config_subcategory.name),self.option.name)

	async def generate_embed(self) -> None:
		embed_color = int((await self.client.db.guild(self.user.guild.id)).config.general.embed_color,16)
		self.master.embed_color = embed_color
		self.embed = Embed(
			title=f'{self.option.name}',color=self.master.embed_color,
			description=self.option.description)
		match self.config_category.name:
			case 'user': self.embed.set_author(name=self.user.display_name,icon_url=self.user.avatar.url)
			case 'guild': self.embed.set_author(name=self.user.guild.name,icon_url=self.user.guild.icon.url)
			case 'dev': self.embed.set_author(name=self.client.user.display_name,icon_url=self.client.user.avatar.url)
			case _: raise ValueError('improper config category name')
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

		current_value = await self.current_value()

		self.get_item('button_true').style = ButtonStyle.green if current_value else ButtonStyle.red
		self.get_item('button_false').style = ButtonStyle.green if not current_value else ButtonStyle.red

	async def handle_twbf(self) -> None:
		self.add_item(self.button_true)
		self.add_item(self.button_whitelist)
		self.add_item(self.button_blacklist)
		self.add_item(self.button_false)

		self.get_item('button_true').style = ButtonStyle.blurple
		self.get_item('button_whitelist').style = ButtonStyle.blurple
		self.get_item('button_blacklist').style = ButtonStyle.blurple
		self.get_item('button_false').style = ButtonStyle.blurple

		match await self.current_value():
			case TWBFMode.true: self.get_item('button_true').style = ButtonStyle.green
			case TWBFMode.whitelist: self.get_item('button_whitelist').style = ButtonStyle.green
			case TWBFMode.blacklist: self.get_item('button_blacklist').style = ButtonStyle.green
			case TWBFMode.false: self.get_item('button_false').style = ButtonStyle.green
			case _: raise ValueError('improper twbf mode')


	async def handle_string(self) -> None:
		self.add_item(self.button_set_string)

	async def handle_int(self) -> None:
		pass

	async def handle_float(self) -> None:
		pass

	async def handle_channel(self) -> None:
		pass

	async def handle_role(self) -> None:
		pass

	async def handle_user(self) -> None:
		pass

	async def validate_bool(self,value:bool) -> tuple[ValidOption,Any|tuple[str,Any]]:
		if self.config_category.name == 'user' and self.option.name == 'no_track' and value: await handle_user_no_track(self.user)
		return (ValidOption.true,value)
	
	async def validate_twbf(self,value:TWBFMode) -> tuple[ValidOption,Any|tuple[str,Any]]:
		return (ValidOption.true,value)

	async def validate_string(self,value:str) -> tuple[ValidOption,Any|tuple[str,Any]]:
		if self.option.attrs.regex and not match(self.option.attrs.regex,value,IGNORECASE): return (ValidOption.false,f'failed to match regex `{self.option.attrs.regex}`')

		if self.option.name == 'embed_color' and value.startswith('#'): value = value[1:]
		return (ValidOption.true,value)

	async def validate_int(self,value:int) -> tuple[ValidOption,Any|tuple[str,Any]]:
		if self.option.attrs.max_value and value > self.option.attrs.max_value: return (ValidOption.false,f'value cannot be greater than `{self.option.attrs.max_value}`')
		if self.option.attrs.min_value and value < self.option.attrs.min_value: return (ValidOption.false,f'value cannot be less than `{self.option.attrs.min_value}`')
		return (ValidOption.true,value)
	
	async def validate_float(self,value:float) -> tuple[ValidOption,Any|tuple[str,Any]]:
		return await self.validate_int(value)
	
	async def validate_channel(self,value:GuildChannel) -> tuple[ValidOption,str]:
		if self.config_category.name == 'guild' and self.option.name == 'channel':
			match self.config_subcategory.name:
				case 'qotd': return await validate_qotd_channel(self.user,value)
				case 'tts'|'logging'|'talking_stick' if value.type != ChannelType.text:
					return (ValidOption.false,'channel must be a text channel')
		return (ValidOption.true,value)
	
	async def validate_role(self,value:Role) -> tuple[ValidOption,str]:
		return (ValidOption.true,value)
	
	async def validate_user(self,value:Member) -> tuple[ValidOption,str]:
		return (ValidOption.true,value)

	async def write_config(self,value:Any) -> str|None:
		match self.option.type:
			case OptionType.BOOL: valid_value = await self.validate_bool(value)
			case OptionType.TWBF: valid_value = await self.validate_twbf(value)
			case OptionType.STRING: valid_value = await self.validate_string(value)
			case OptionType.INT: valid_value = await self.validate_int(value)
			case OptionType.FLOAT: valid_value = await self.validate_float(value)
			case OptionType.CHANNEL: valid_value = await self.validate_channel(value)
			case OptionType.ROLE: valid_value = await self.validate_role(value)
			case OptionType.USER: valid_value = await self.validate_user(value)
			case _: raise ValueError('improper option type')
		match list(valid_value):
			case [ValidOption.true,return_value]: value = return_value
			case [ValidOption.warn,(warning,return_value)]: value = return_value
			case [ValidOption.false,error]: raise ValueError(error)
		setattr(getattr(self.object_doc.config,self.config_subcategory.name),self.option.name,value)
		await self.object_doc.save_changes()
		await self.client.log.info(f'{self.user.name} set {self.config_category.name}.{self.config_subcategory.name}.{self.option.name} to {value}',
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
		if warning is not None: await interaction.followup.send(Embed(
			title='warning!',color=0xffff69,
			description=warning),ephemeral=True)
	
	@button(
		label='true',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_true')
	async def button_true(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(True if self.option.type == OptionType.BOOL else TWBFMode.true)
		await interaction.response.edit_message(embed=self.embed,view=self)
		if warning is not None: await interaction.followup.send(Embed(
			title='warning!',color=0xffff69,
			description=warning),ephemeral=True)
	
	@button(
		label='false',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_false')
	async def button_false(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(False if self.option.type == OptionType.BOOL else TWBFMode.false)
		await interaction.response.edit_message(embed=self.embed,view=self)
		if warning is not None: await interaction.followup.send(Embed(
			title='warning!',color=0xffff69,
			description=warning),ephemeral=True)

	@button(
		label='whitelist',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_whitelist')
	async def button_whitelist(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(TWBFMode.whitelist)
		await interaction.response.edit_message(embed=self.embed,view=self)
		if warning is not None: await interaction.followup.send(Embed(
			title='warning!',color=0xffff69,
			description=warning),ephemeral=True)
	
	@button(
		label='blacklist',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_blacklist')
	async def button_blacklist(self,button:Button,interaction:Interaction) -> None:
		warning = await self.write_config(TWBFMode.blacklist)
		await interaction.response.edit_message(embed=self.embed,view=self)
		if warning is not None: await interaction.followup.send(Embed(
			title='warning!',color=0xffff69,
			description=warning),ephemeral=True)
	
	@button(
		label='configure channels',row=3,
		style=ButtonStyle.blurple,
		custom_id='button_configure_channels')
	async def button_configure_channels(self,button:Button,interaction:Interaction) -> None:
		...
	
	@button(
		label='set',row=2,
		style=ButtonStyle.blurple,
		custom_id='button_set_string')
	async def button_set_string(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(
			f'set {self.option.name}',
			[InputText(
				label=self.option.name,
				placeholder=self.option.attrs.placeholder,
				max_length=self.option.attrs.max_length,
				min_length=self.option.attrs.min_length,
				custom_id='input_set'
		)])
		
		await interaction.response.send_modal(modal)

		await modal.wait()
		warning = await self.write_config(modal.children[0].value)
		await modal.interaction.response.edit_message(embed=self.embed,view=self)
		if warning is not None: await interaction.followup.send(Embed(
			title='warning!',color=0xffff69,
			description=warning),ephemeral=True)
