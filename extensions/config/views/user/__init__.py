from discord import Interaction,Embed,SelectOption,User,Member as DiscordMember
from discord.ui import Button,button,Select,string_select,InputText
from extensions._shared_vars import config_info,valid_voices
from client import Client,EmptyView,CustomModal,MixedUser
from utils.pluralkit import Member as PKMember
from asyncio import create_task

class user_config(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,user:User,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.back_view    = back_view
		self.client       = client
		self.discord_user = user
		self.user         = user
		self.embed        = Embed(title='user config',color=embed_color or back_view.embed.color)
		self.config       = {}
		self.category     = None
		self.selected     = None
		self.pk_members   = None
		self.embed.set_author(name=self.user.name,icon_url=self.user.icon or 'https://regn.al/discord.png')
		if back_view is not None: self.add_item(self.back_button)
		self.add_items(self.category_select,self.pluralkit_button)

	@property
	def config_type(self) -> str|None:
		return config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.category,{}).get(self.selected,{}).get('type',None)

	async def start(self) -> bool:
		pass

	@property
	def user(self) -> MixedUser:
		return self._user

	@user.setter
	def user(self,user:(User|DiscordMember)|PKMember) -> None:
		if isinstance(user,User|DiscordMember): # discord user
			self._user = MixedUser('discord',user,id=user.id,name=user.name,icon=user.avatar.url if user.avatar else None)
		elif isinstance(user,PKMember): # pluralkit system
			self._user = MixedUser('pluralkit',user,id=user.uuid,name=user.name,icon=user.avatar_url)
		else: raise ValueError('user type must be discord User or PluralKit Member')

	def reload_embed(self) -> None:
		self.embed.clear_fields()
		self.embed.set_author(name=self.user.name,icon_url=self.user.icon or 'https://regn.al/discord.png')
		category_data = config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.category,{})
		for k,v in self.config.get(self.category,{}).items():
			if self.user.type == 'pluralkit' and k not in config_info.get('pk_user',{}).get(self.category,{}).keys(): continue
			self.embed.add_field(name=k,value=v)
		if self.selected is None: self.embed.description = None
		else: self.embed.description = category_data.get(self.selected,{}).get('description',None)

	async def reload_config(self) -> None:
		try: self.config = await self.client.db.user(self.user.id).config.read()
		except TypeError: await self.create_pk_doc()
		else:
			if self.config is None: await self.create_pk_doc()
		finally: self.config = await self.client.db.user(self.user.id).config.read()
		options = [SelectOption(label=k,description=v.get('description','').split('\n')[0][:100]) for k,v in config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.category,{}).items()]
		for option in options: option.default = option.label == self.selected
		self.get_item('option_select').options = options

	async def write_config(self,value:bool|str,interaction:Interaction=None) -> None:
		match self.selected:
			case 'no_track' if self.category == 'general':
				if value:
					await self.client.db.user(self.user.id).messages.write(None)
					await self.client.db.user(self.user.id).data.au.write({'contains':[],'exact':[],'exact_cs':[]})
					for guild in self.discord_user.mutual_guilds:
						await self.client.db.guild(guild.id).data.leaderboards.messages.unset([str(self.user.id)])
						await self.client.db.guild(guild.id).data.leaderboards.sticks.unset([str(self.user.id)])
				else: await self.client.db.user(self.user.id).messages.write(0)
			case 'voice' if self.category == 'tts' and value is not None:
				if (value:=value.strip()) not in valid_voices:
					create_task(interaction.followup.send(embed=Embed(
						title='ERROR: invalid voice selected',
						description=f'find and test voices [here](<https://cloud.google.com/text-to-speech#section-2>)\nthe voice is the option in the \"Voice Name\" section\ne.g. \"en-US-Neural2-H\" or \"de-DE-Neural2-D\"',color=0xff6969),ephemeral=True))
					return
			case 'speaking_rate' if self.category == 'tts':
				if not 0.25 < (value:=float(value)) <= 4:
					create_task(interaction.followup.send(embed=Embed(
						title='ERROR: invalid speaking_rate selected',
						description=f'please pick a number between 0.25 and 4.00',color=0xff6969),ephemeral=True))
					return

		await self.client.db.user(self.user.id).config.write(value,[self.category,self.selected])
		await self.reload_config()
		self.reload_embed()

	@button(
		label='<',style=2,
		custom_id='back_button',row=2)
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		if self.category is None and self.selected != 'pk':
			await interaction.response.edit_message(view=self.back_view,embed=self.back_view.embed)
			self.stop()
			return
		self.category = None
		self.selected = None
		self.embed.title = 'user config'
		self.embed.description = None
		self.embed.clear_fields()
		self.clear_items()
		if self.back_view is not None: self.add_item(self.back_button)
		if self.pk_members != []: self.add_item(self.pluralkit_button)
		self.add_item(self.category_select)
		await interaction.response.edit_message(view=self,embed=self.embed)

	@string_select(
		placeholder='select a config category',
		custom_id='category_select',row=0,
		options=[
			SelectOption(label='general',description='general options'),
			SelectOption(label='tts',description='text-to-speech options')])
	async def category_select(self,select:Select,interaction:Interaction) -> None:
		self.category = select.values[0]
		self.clear_items()
		self.add_items(self.back_button,self.option_select)
		await self.reload_config()
		self.reload_embed()
		await interaction.response.edit_message(view=self,embed=self.embed)

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
				case 'ewbd':
					self.add_items(self.enable_button,self.whitelist_button,self.blacklist_button,self.disable_button)
					if (mode:=self.config.get(self.selected,None)) in ['whitelist','blacklist']:
						self.add_item(self.configure_list_button)
						self.get_item('configure_list_button').label = f'configure {mode}'
				case 'modal': self.add_item(self.modal_button)
				case 'select':
					data = config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.category,{}).get(self.selected,{})
					self.add_item(self.select_select)
					self.get_item('select_select').placeholder = data.get('label','select an option')
					self.get_item('select_select').options = [SelectOption(label=k,description=v) for k,v in data.get('options')]
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

	@string_select(custom_id='select_select',row=1)
	async def select_select(self,select:Select,interaction:Interaction) -> None:
		await self.write_config(select.values[0])
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='enable',style=3,
		custom_id='enable_button',row=2)
	async def enable_button(self,button:Button,interaction:Interaction) -> None:
		match self.config_type:
			case 'ewbd': await self.write_config('enabled')
			case 'bool': await self.write_config(True)
			case _     : raise
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='whitelist',style=1,
		custom_id='whitelist_button',row=2)
	async def whitelist_button(self,button:Button,interaction:Interaction) -> None:
		if self.get_item('configure_list_button') is None: self.add_item(self.configure_list_button)
		self.get_item('configure_list_button').label = f'configure whitelist'
		await self.write_config('whitelist')
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='blacklist',style=1,
		custom_id='blacklist_button',row=2)
	async def blacklist_button(self,button:Button,interaction:Interaction) -> None:
		if self.get_item('configure_list_button') is None: self.add_item(self.configure_list_button)
		self.get_item('configure_list_button').label = f'configure blacklist'
		await self.write_config('blacklist')
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='disable',style=4,
		custom_id='disable_button',row=2)
	async def disable_button(self,button:Button,interaction:Interaction) -> None:
		match self.config_type:
			case 'ewbd': await self.write_config('disabled')
			case 'bool': await self.write_config(False)
			case _     : raise
		await interaction.response.edit_message(embed=self.embed,view=self)
	
	@button(
		label='set',style=1,
		custom_id='modal_button',row=2)
	async def modal_button(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(self,f'set {self.selected}',
			[InputText(label=self.selected,
				max_length=config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.category,{}).get(self.selected,{}).get('max_length',None))])
		await interaction.response.send_modal(modal)
		await modal.wait()
		await self.write_config(modal.children[0].value,interaction)
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='reset to default',style=4,
		custom_id='reset_button',row=3)
	async def reset_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.category,{}).get(self.selected,{}).get('default',None))
		await interaction.response.edit_message(view=self,embed=self.embed)

	@string_select(
		placeholder='select a member',
		custom_id='pk_select',row=0)
	async def pk_select(self,select:Select,interaction:Interaction) -> None:
		user = [m for m in self.pk_members if m.uuid == select.values[0]] or [self.discord_user]
		self.user = user[0]
		self.embed.title = 'user config'
		self.clear_items()
		if self.back_view is not None: self.add_item(self.back_button)
		if self.pk_members: self.add_item(self.pluralkit_button)
		match self.user.type:
			case 'pluralkit':
				self.add_item(self.option_select)
				self.category = 'general'
			case 'discord':
				self.add_item(self.category_select)
		await self.reload_config()
		self.reload_embed()
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='change user (pluralkit)',style=2,
		custom_id='pluralkit_button',row=4)
	async def pluralkit_button(self,button:Button,interaction:Interaction) -> None:
		if self.pk_members is None:
			self.pk_members = await self.client.pk.get_members(self.discord_user.id)
		self.selected = 'pk'
		self.clear_items()
		self.embed.title = 'select a member'
		self.embed.description = None
		self.embed.clear_fields()
		self.add_item(self.back_button)
		if self.pk_members:
			self.add_item(self.pk_select)
			self.get_item('pk_select').options = [
				SelectOption(label=f'[DISCORD] {self.discord_user.name}',value=str(self.discord_user.id),default=self.user.id == self.discord_user.id)]+[
				SelectOption(label=m.name,value=m.uuid,default=self.user.id==m.uuid) for m in self.pk_members]
		else:
			self.embed.description = 'you have no pluralkit members'
			button.disabled = True
		await interaction.response.edit_message(view=self,embed=self.embed)