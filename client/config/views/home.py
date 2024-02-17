from discord import Interaction,SelectOption,User,Member,Embed
from utils.db.documents.ext.flags import UserFlags
from utils.pycord_classes import SubView,MasterView
from discord.ui import string_select,Select
from .category import ConfigCategoryView


class ConfigHomeView(SubView):
	def __init__(self,master:'MasterView',user:User|Member,**kwargs) -> None:
		super().__init__(master,**kwargs)
		self.add_item(self.category_select)
		self.user = user

	async def __ainit__(self) -> None:
		options = [
			SelectOption(label='user',description='user config')]

		is_dev = self.user.id in self.master.client.owner_ids and self.master.client.project.config.dev_bypass
		is_bot_admin = (await self.master.client.db.user(self.user.id)).data.flags & UserFlags.ADMIN

		if getattr(self.user,'guild',None) is not None:
			match (await self.master.client.db.guild(self.user.guild.id)).config.permissions.advanced:
				case True: has_permission = bool(await self.master.client.permissions.user(self.user,self.user.guild))
				case False: has_permission = self.user.guild_permissions.manage_guild
				case _: raise ValueError('thAT\'S NOT HOW BOOLEANS WORK')

			if has_permission:# or is_dev or is_bot_admin:
				options.append(SelectOption(label='guild',description='guild config'))
		if is_dev or is_bot_admin:
			options.append(SelectOption(label='dev',description='dev config'))
		self.get_item('category_select').options = options
		self.embed = Embed(
			title='config',color=self.master.embed_color)
		self.embed.set_footer(text=f'config')

	@string_select(
		placeholder='select a config category',
		custom_id='category_select')
	async def category_select(self,select:Select,interaction:Interaction) -> None:
		match select.values[0]:
			case 'user':
				view = self.master.create_subview(ConfigCategoryView,self.client.config.data.user,user=self.user)
			case 'guild':
				view = self.master.create_subview(ConfigCategoryView,self.client.config.data.guild,user=self.user)
			case 'dev':
				view = self.master.create_subview(ConfigCategoryView,self.client.config.data.dev,user=self.user)
			case _: raise ValueError('improper option selected, discord shouldn\'t allow this')
		await view.__ainit__()
		await interaction.response.edit_message(view=view,embed=view.embed)