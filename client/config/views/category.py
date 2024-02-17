from discord import Interaction,SelectOption,User,Member,Embed
from utils.db.documents.ext.flags import UserFlags
from utils.pycord_classes import SubView,MasterView
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
		self.add_item(self.back_button)
		options = []
		user_permissions = await self.master.client.permissions.user(self.user,self.user.guild)
		is_dev = self.user.id in self.master.client.owner_ids and self.master.client.project.config.dev_bypass
		is_bot_admin = (await self.master.client.db.user(self.user.id)).data.flags & UserFlags.ADMIN

		for subcategory in self.config_category.subcategories:
			if (
				(is_dev or is_bot_admin) or 
				not self.master.client.permissions.matcher(f'{subcategory.name}*',user_permissions)
			):
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
			case 'user': self.embed.set_author(name=self.user.display_name,icon_url=self.user.avatar.url)
			case 'guild': self.embed.set_author(name=self.user.guild.name,icon_url=self.user.guild.icon.url)
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