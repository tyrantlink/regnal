from discord import Interaction,Embed,SelectOption,Member,User,Guild
from discord.ui import Select,string_select
from utils.classes import EmptyView
from .guild import guild_config
from .user import user_config
from .dev import dev_menu
from client import Client

class config_view(EmptyView):
	def __init__(self,client:Client,user:Member|User,guild:Guild,dev_bypass:bool,moderator_role:int|None,embed_color:int) -> None:
		super().__init__(timeout=0)
		self.client = client
		self.user   = user
		self.guild  = guild
		self.dev_bypass = dev_bypass
		self.moderator_role = moderator_role
		self.embed = Embed(title='config',color=embed_color)
		self.add_item(self.option_select)
		self.populate_options()

	def populate_options(self) -> None:
		self.options = [SelectOption(label='user',description='user specific options')]
		if self.guild is not None:
			if (self.user.guild_permissions.manage_guild or
				(self.dev_bypass and self.user.id in self.client.owner_ids) or
				(self.user.get_role(self.moderator_role) if self.moderator_role else False)):
				self.options.append(SelectOption(label='guild',description='guild config menu'))
		if self.user.id == self.client.owner_id:
			self.options.append(SelectOption(label='dev',description='dev options'))
		self.get_item('option_select').options = self.options

	@string_select(
		placeholder='place select a config category',
		custom_id='option_select')
	async def option_select(self,select:Select,interaction:Interaction) -> None:
		match select.values[0]:
			case 'user':  view = user_config(self,self.client,self.user)
			case 'guild': view = guild_config(self,self.client,self.user,self.guild)
			case 'dev':   view = dev_menu(self,self.client)
			case _: raise ValueError('improper option selected, discord shouldn\'t allow this')
		await interaction.response.edit_message(view=view,embed=view.embed)
