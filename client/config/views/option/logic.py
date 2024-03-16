from client.config.errors import ConfigValidationError
from client.config.models import OptionType
from .typehint import ConfigOptionTypeHint
from discord import Embed,Interaction
from typing import Any


class ConfigOptionLogic(ConfigOptionTypeHint):
	def current_value(self) -> Any:
		return getattr(getattr(self.object_doc.config,self.config_subcategory.name),self.option.name)

	def _convert_to_mention(self,value:Any) -> str:
		if value not in {'None',None}:
			match self.option.type:
				case OptionType.CHANNEL: return f'<#{value}>'
				case OptionType.ROLE   : return f'<@&{value}>'
				case OptionType.USER   : return f'<@{value}>'
		return str(value)

	def current_value_printable(self) -> str:
		value = self.current_value()
		return (
			'\n'.join([self._convert_to_mention(i) for i in value]) or 'None'
			if self.option.attrs.multi else
			self._convert_to_mention(value))

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

	async def write_config(self,value:Any,interaction:Interaction) -> str|None:
		try:
			warning = None
			if value is not None:
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
				if self.option.attrs.validation is not None:
					value,warning = await self.option.attrs.validation(self.client,self.option,value,self.user)
			elif not self.option.nullable: raise ConfigValidationError('value cannot be None')
		except ConfigValidationError as e:
			e.add_note('suppress')
			raise e

		if (
			self.option.type in {OptionType.CHANNEL,OptionType.ROLE,OptionType.USER}
			and not self.option.attrs.multi
		): value = value.id if value else None

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
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.give_warning(interaction,warning)