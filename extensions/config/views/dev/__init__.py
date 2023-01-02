from discord.ui import Button,button,Select,string_select,InputText,channel_select
from discord import Interaction,Embed,SelectOption
from extensions._shared_vars import config_info
from client import Client,EmptyView,CustomModal
from utils.tyrantlib import MakeshiftClass
from ..guild import guild_config
from ..user import user_config

class dev_menu(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.back_view    = back_view
		self.client       = client
		self.embed        = Embed(title='dev config',color=embed_color or back_view.embed.color)
		self.selected     = None
		self.embed.set_author(name=self.client.user.name,icon_url=self.client.user.avatar.url)
		if back_view is not None: self.add_item(self.back_button)
		self.add_items(self.category_select)

	@property
	def config_type(self) -> str|None:
		return config_info.get('dev',{}).get(self.selected,{}).get('type',None)

	async def start(self) -> bool:
		pass

	async def impersonate(self,category:str,interaction:Interaction) -> tuple[user_config|guild_config,Interaction]:
		modal = CustomModal(self,f'input {category} id',[InputText(label=f'{category} id')])
		await interaction.response.send_modal(modal)
		await modal.wait()
		_id = int(modal.children[0].value)
		match category:
			case 'user':  view = user_config(self,self.client,self.client.get_user(_id) or await self.client.fetch_user(_id))
			case 'guild': view = guild_config(self,self.client,MakeshiftClass(id=self.client.owner_id),self.client.get_guild(_id) or await self.client.fetch_guild(_id,with_counts=False))
		return (view,modal.interaction)

	def reload_embed(self) -> None:
		self.embed.clear_fields()
		config_data = config_info.get('dev',{})
		for k,v in self.config.items():
			if v is not None:
				match config_data.get(k,{}).get('type'):
					case 'channel': v = f'<#{v}>'
					case 'role'   : v = f'<@&{v}>'
			self.embed.add_field(name=k,value=v)
		if self.selected is None: self.embed.description = None
		else: self.embed.description = config_data.get(self.selected,{}).get('description',None)

	async def reload_config(self) -> None:
		self.config = await self.client.db.inf.read('/reg/nal',['config'])
		options = [SelectOption(label=k,description=v.get('description','').split('\n')[0][:100]) for k,v in config_info.get('dev',{}).items()]
		for option in options: option.default = option.label == self.selected
		self.get_item('option_select').options = options

	async def write_config(self,value) -> None:
		await self.client.db.inf.write('/reg/nal',['config',self.selected],value)
		await self.reload_config()
		self.reload_embed()

	@button(
		label='<',style=2,
		custom_id='back_button',row=2)
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		if self.category is None:
			await interaction.response.edit_message(view=self.back_view,embed=self.back_view.embed)
			self.stop()
			return
		self.category = None
		self.selected = None
		self.embed.title = 'dev config'
		self.embed.description = None
		self.embed.clear_fields()
		self.clear_items()
		if self.back_view is not None: self.add_item(self.back_button)
		self.add_item(self.category_select)
		await interaction.response.edit_message(view=self,embed=self.embed)

	@string_select(
		placeholder='select a config category',
		custom_id='category_select',row=0,options=[
			SelectOption(label='general'),
			# SelectOption(label='extensions'),
			# SelectOption(label='auto responses'),
			SelectOption(label='user config'),
			SelectOption(label='guild config')])
	async def category_select(self,select:Select,interaction:Interaction) -> None:
		self.category = select.values[0]
		match select.values[0]:
			case 'general':
				self.clear_items()
				self.add_items(self.back_button,self.option_select)
				await self.reload_config()
				self.reload_embed()
				view = self
			# case 'extensions': view = None
			# case 'auto responses': view = None
			case 'user config'|'guild config': view,interaction = await self.impersonate(select.values[0].split()[0],interaction)
			case _: raise ValueError('improper option selected, discord shouldn\'t allow this')
		await view.start()
		await interaction.response.edit_message(view=view,embed=view.embed)

	@string_select(
		placeholder='select an option',
		custom_id='option_select',row=0,min_values=0)
	async def option_select(self,select:Select,interaction:Interaction) -> None:
		self.clear_items()
		if select.values:
			self.selected = select.values[0]
			self.reload_embed()
			self.add_items(self.back_button,self.option_select,self.reset_button)
			match self.config_type:
				case 'bool': self.add_items(self.enable_button,self.disable_button)
				case 'channel': self.add_item(self.channel_select)
				case _: raise
			options = select.options.copy()
			for option in options: option.default = option.label == self.selected
			select.options = options
		else:
			self.selected = None
			self.reload_embed()
			self.add_items(self.back_button,self.option_select)
			for option in select.options: option.default = False
		await interaction.response.edit_message(view=self,embed=self.embed)

	@channel_select(
		placeholder='select a channel',
		custom_id='channel_select',row=1,min_values=0)
	async def channel_select(self,select:Select,interaction:Interaction) -> None:
		if not select.values:
			await self.write_config(None)
			await interaction.response.edit_message(embed=self.embed,view=self)
			return
		if select.values[0].type.name == 'forum':
			if self.selected not in ['support']: 
				await interaction.response.edit_message(embed=self.embed,view=self)
				await interaction.followup.send(ephemeral=True,embed=Embed(title='error!',color=0xff6969,
					description=f'forum channels are not supported for option type `{self.selected}`'))
				return
		elif not select.values[0].can_send():
			await interaction.followup.send(ephemeral=True,embed=Embed(title='warning!',color=0xffff69,
				description=f'i don\'t have permission to send messages in {select.values[0].mention}\nthe channel will still be set, but you should probably fix that.'))
		await self.write_config(select.values[0].id)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='enable',style=3,
		custom_id='enable_button',row=2)
	async def enable_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(True)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='disable',style=4,
		custom_id='disable_button',row=2)
	async def disable_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(False)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='reset to default',style=4,
		custom_id='reset_button',row=3)
	async def reset_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(config_info.get('dev',{}).get(self.selected,{}).get('default',None))
		await interaction.response.edit_message(view=self,embed=self.embed)