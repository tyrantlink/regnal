from discord import Interaction,SelectOption,User,Member,Embed
from ..models import ConfigCategory,ConfigSubcategory,OptionType
from utils.db.documents.ext.flags import UserFlags
from utils.pycord_classes import SubView,MasterView
from discord.ui import string_select,Select
from .option import ConfigOptionView


class ConfigSubcategoryView(SubView):
	def __init__(self,
							master:'MasterView',
							config_category:ConfigCategory,
							config_subcategory:ConfigSubcategory,
							user:User|Member,
	**kwargs) -> None:
		super().__init__(master,**kwargs)
		self.config_category = config_category
		self.config_subcategory = config_subcategory
		self.user = user
		self.generate_embed()

	async def __ainit__(self) -> None:
		self.add_item(self.back_button)
		self.add_item(self.option_select)
		match self.config_category.name:
			case 'user': current_config = getattr((await self.client.db.user(self.user.id)).config,self.config_subcategory.name)
			case 'guild': current_config = getattr((await self.client.db.guild(self.user.guild.id)).config,self.config_subcategory.name)
			case 'dev': raise NotImplementedError('dev config not implemented yet!')
		options = []

		for option in self.config_subcategory.options:
			match self.config_category.name:
				case 'user':
					pass
				case 'guild' if await self.client.permissions.check(f'{self.config_subcategory.name}*',self.user,self.user.guild):
					pass
				case 'dev' if await self.client.permissions.check('dev',self.user,self.user.guild):
					pass
				case _: continue

			options.append(SelectOption(label=option.name,description=option.short_description))
			value = str(getattr(current_config,option.name))
			if value not in  {'None',None}:
				match option.type:
					case OptionType.CHANNEL: value = f'<#{value}>'
					case OptionType.ROLE: value = f'<@&{value}>'
					case OptionType.USER: value = f'<@{value}>'
					case _: pass
			self.embed.add_field(name=option.name,value=value)

		if options:
			self.get_item('option_select').options = options
			return

		self.get_item('option_select').options = [SelectOption(label='None')]
		self.get_item('option_select').placeholder = 'no access'
		self.get_item('option_select').disabled = True


	async def __on_back__(self) -> None:
		self.generate_embed()
		self.clear_items()
		await self.__ainit__()

	def generate_embed(self) -> None:
		self.embed = Embed(
			title=f'{self.config_subcategory.name} config',color=self.master.embed_color)
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
		self.embed.set_footer(text=f'config.{self.config_category.name}.{self.config_subcategory.name}')

	@string_select(
		placeholder='select an option',
		custom_id='option_select')
	async def option_select(self,select:Select,interaction:Interaction) -> None:
		option = self.config_subcategory[select.values[0]]
		view = self.master.create_subview(ConfigOptionView,self.config_category,self.config_subcategory,option,self.user)
		await view.__ainit__()
		await interaction.response.edit_message(view=view,embed=view.embed)