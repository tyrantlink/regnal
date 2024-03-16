from discord import Interaction,SelectOption,User,Member,Embed
from utils.pycord_classes import SubView,MasterView
from .additional_view import AdditionalViewButton
from .subcategory import ConfigSubcategoryView
from discord.ui import string_select,Select
from ..models import ConfigCategory


class ConfigCategoryView(SubView):
	def __init__(self,master:'MasterView',config_category:ConfigCategory,user:User|Member,**kwargs) -> None:
		super().__init__(master,**kwargs)
		self.config_category = config_category
		self.user = user
		self.add_item(self.subcategory_select)
		self.generate_embed()

	async def __ainit__(self) -> None:
		if len(self.master.views) > 1: self.add_item(self.back_button)

		for view in self.config_category.additional_views:
			if view.required_permissions is not None:
				match self.config_category.name:
					case 'user':
						pass
					case 'guild' if await self.client.permissions.check(view.required_permissions,self.user,self.user.guild):
						pass
					case 'dev' if await self.client.permissions.check('dev',self.user,self.user.guild):
						pass
					case _: continue
			view_button = AdditionalViewButton(self,view)
			self.add_item(view_button)

		options = []

		for subcategory in self.config_category.subcategories:
			match self.config_category.name:
				case 'user':
					pass
				case 'guild' if await self.client.permissions.check(f'{subcategory.name}*',self.user,self.user.guild):
					pass
				case 'dev' if await self.client.permissions.check('dev',self.user,self.user.guild):
					pass
				case _: continue

			options.append(SelectOption(label=subcategory.name,description=subcategory.description))

		if options:
			self.get_item('subcategory_select').options = options
			return

		self.get_item('subcategory_select').options = [SelectOption(label='None')]
		self.get_item('subcategory_select').placeholder = 'no access'
		self.get_item('subcategory_select').disabled = True


	def generate_embed(self) -> None:
		self.embed = Embed(
			title=f'{self.config_category.name} config',color=self.master.embed_color)
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
		self.embed.set_footer(text=f'config.{self.config_category.name}')

	@string_select(
		placeholder='select a subcategory',
		custom_id='subcategory_select')
	async def subcategory_select(self,select:Select,interaction:Interaction) -> None:
		subcategory = self.config_category[select.values[0]]

		view = self.master.create_subview(ConfigSubcategoryView,self.config_category,subcategory,self.user)
		await view.__ainit__()
		await interaction.response.edit_message(view=view,embed=view.embed)