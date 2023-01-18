from discord import Interaction,Embed,User,SelectOption,Member as DiscordMember
from discord.ui import Button,button,Select,string_select
from extensions._shared_vars import config_info
from utils.pluralkit import Member as PKMember
from client import EmptyView,Client,MixedUser

class user_config(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,user:User,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.back_view    = back_view
		self.client       = client
		self.discord_user = user
		self.user         = user
		self.embed        = Embed(title='user config',color=embed_color or back_view.embed.color)
		self.config       = {}
		self.selected     = None
		self.pk_members   = None
		if back_view is not None: self.add_item(self.back_button)
		self.add_items(self.option_select,self.pluralkit_button)

	async def start(self) -> bool:
		await self.reload_config()
		self.reload_embed()
	
	async def create_pk_doc(self):
		await self.client.db.users.new(self.user.id)
		await self.client.db.users.write(self.user.id,['username'],self.user.name)
		await self.client.db.users.write(self.user.id,['pluralkit'],True)
		await self.client.db.users.write(self.user.id,['config','talking_stick'],False)

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
		self.embed.set_author(name=self.user.name,icon_url=self.user.icon or 'https://regn.al/discord.png')
		self.embed.clear_fields()
		for k,v in self.config.items():
			if self.user.type == 'pluralkit' and k in ['hide_commands','talking_stick']: continue
			self.embed.add_field(name=k,value=v)
		if self.selected is None or self.selected == 'pk': self.embed.description = None
		else: self.embed.description = config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.selected,{}).get('description',None)

	async def reload_config(self) -> None:
		try: self.config = await self.client.db.users.read(self.user.id,['config'])
		except TypeError: await self.create_pk_doc()
		else:
			if self.config is None: await self.create_pk_doc()
		finally: self.config = await self.client.db.users.read(self.user.id,['config'])
		options = [SelectOption(label=k,description=v.get('description','').split('\n')[0][:100]) for k,v in config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).items()]
		for option in options: option.default = option.label == self.selected
		self.get_item('option_select').options = options
	
	async def write_config(self,value:bool) -> None:
		match self.selected:
			case 'no_track' if value:
				await self.client.db.users.write(self.user.id,['messages'],None)
				await self.client.db.users.write(self.user.id,['data','au'],{'contains':[],'exact':[],'exact-cs':[]})
				for guild in self.discord_user.mutual_guilds:
					await self.client.db.guilds.unset(guild.id,['data','leaderboards','messages',str(self.user.id)])
					await self.client.db.guilds.unset(guild.id,['data','leaderboards','sticks',str(self.user.id)])
				
				else: await self.client.db.users.write(self.user.id,['messages'],0)

		await self.client.db.users.write(self.user.id,['config',self.selected],value)
		await self.reload_config()
		self.reload_embed()

	@button(
		label='<',style=2,
		custom_id='back_button',row=1)
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		if self.selected == 'pk':
			self.selected = None
			self.embed.title = 'user config'
			self.reload_embed()
			self.clear_items()
			if self.back_view is not None: self.add_item(self.back_button)
			if self.pk_members: self.add_item(self.pluralkit_button)
			self.add_item(self.option_select)
			await interaction.response.edit_message(view=self,embed=self.embed)
		else:
			await interaction.response.edit_message(view=self.back_view,embed=self.back_view.embed)
			self.stop()

	@string_select(
		placeholder='select an option',
		custom_id='option_select',row=0,min_values=0)
	async def option_select(self,select:Select,interaction:Interaction) -> None:
		self.clear_items()
		if select.values:
			self.selected = select.values[0]
			self.reload_embed()
			self.add_items(self.option_select,self.back_button,self.enable_button,self.disable_button,self.reset_button)
			options = select.options.copy()
			for option in options: option.default = option.label == self.selected
			select.options = options
		else:
			self.selected = None
			self.reload_embed()
			for option in select.options: option.default = False
			self.add_items(self.option_select,self.back_button)
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='enable',style=3,
		custom_id='enable_button',row=1)
	async def enable_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(True)
		await interaction.response.edit_message(view=self,embed=self.embed)


	@button(
		label='disable',style=4,
		custom_id='disable_button',row=1)
	async def disable_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(False)
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='reset to default',style=4,
		custom_id='reset_button',row=2)
	async def reset_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(config_info.get('user' if self.user.type == 'discord' else 'pk_user',{}).get(self.selected,{}).get('default',False))
		await interaction.response.edit_message(view=self,embed=self.embed)

	@string_select(
		placeholder='select a member',
		custom_id='pk_select',row=0)
	async def pk_select(self,select:Select,interaction:Interaction) -> None:
		user = [m for m in self.pk_members if m.uuid == select.values[0]]
		if user == []: user = [self.discord_user]
		self.user = user[0]
		self.embed.title = 'user config'
		self.clear_items()
		if self.back_view is not None: self.add_item(self.back_button)
		if self.pk_members: self.add_item(self.pluralkit_button)
		self.add_item(self.option_select)
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