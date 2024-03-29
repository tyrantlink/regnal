from discord.ui import Button,button,Select,string_select,channel_select,role_select,InputText
from discord import Interaction,Embed,SelectOption,Guild,Member,CategoryChannel
from utils.classes import EmptyView,CustomModal,AutoResponses
from extensions._shared_vars import config_info
from .configure_list import configure_list_view
from .tts_banning import tts_banning_view
from .au_disable import au_disable_view
from discord.abc import GuildChannel
from asyncio import create_task
from client import Client
from ..au import au_view


class guild_config(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,user:Member,guild:Guild,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.back_view   = back_view
		self.client      = client
		self.guild       = guild
		self.user        = user
		self.embed       = Embed(title='guild config',color=embed_color or back_view.embed.color)
		self.config      = {}
		self.category    = None
		self.selected    = None
		self.embed.set_author(name=self.guild.name,icon_url=self.guild.icon.url if self.guild.icon else 'https://regn.al/discord.png')
		if back_view is not None: self.add_item(self.back_button)
		self.add_items(self.category_select)
		self.get_item('category_select').options = [
			SelectOption(label='general',description='general options'),
			SelectOption(label='logging',description='logging config'),
			SelectOption(label='tts',description='text-to-speech config'),
			SelectOption(label='auto_responses',description='auto response config'),
			SelectOption(label='dad_bot',description='dad bot config'),
			SelectOption(label='qotd',description='qotd config'),
			SelectOption(label='talking_stick',description='talking stick config')]

	@property
	def config_type(self) -> str|None:
		return config_info.get('guild',{}).get(self.category,{}).get(self.selected,{}).get('type',None)

	def reload_embed(self) -> None:
		self.embed.clear_fields()
		category_data = config_info.get('guild',{}).get(self.category,{})
		for k,v in self.config.items():
			if v is not None:
				match category_data.get(k,{}).get('type'):
					case 'channel': v = f'<#{v}>'
					case 'role'   : v = f'<@&{v}>'
			self.embed.add_field(name=k,value=v)
		if self.selected is None: self.embed.description = None
		else: self.embed.description = category_data.get(self.selected,{}).get('description',None)

	async def reload_config(self) -> None:
		self.config = await self.client.db.guild(self.guild.id).config.read([self.category])
		options = [SelectOption(label=k,description=v.get('description','').split('\n')[0][:100]) for k,v in config_info.get('guild',{}).get(self.category,{}).items() if v.get('required_permissions',None) is None or self.user.id == self.client.owner_id or getattr(self.user.guild_permissions,v.get('required_permissions'),False)]
		if not options:
			options = [SelectOption(label='None',description='None')]
			self.get_item('option_select').placeholder = 'you do not have permission'
			self.get_item('option_select').disabled = True
		else:
			self.get_item('option_select').disabled = False
			self.get_item('option_select').placeholder = 'select an option'
		for option in options: option.default = option.label == self.selected
		self.get_item('option_select').options = options

	async def validate_channel(self,channel:GuildChannel,interaction:Interaction) -> bool:
		if not channel.permissions_for(self.guild.me).view_channel:
			await interaction.response.send_message(ephemeral=True,embed=Embed(title='warning!',color=0xff6969,
				description=f'i don\'t have permission to view {channel.mention}\nplease correct this and try again\nthis requires the `View Channel` permission'))
			return False
		match self.category:
			case 'qotd':
				if channel.type.name not in ['text','forum']:
					await interaction.response.send_message(ephemeral=True,embed=Embed(title='error!',color=0xff6969,
					description=f'channel type `{channel.type.name}` not supported for channel.type.name `{self.category}`'))
					return False
				if not channel.permissions_for(self.guild.me).send_messages:
					await interaction.response.send_message(ephemeral=True,embed=Embed(title='error!',color=0xff6969,
						description=f'i don\'t have permission to send messages in {channel.mention}\nplease correct this and try again\nthis requires the `Send Messages` permission'))
					return False
				if not channel.permissions_for(self.guild.me).create_public_threads:
					await interaction.response.send_message(ephemeral=True,embed=Embed(title='error!',color=0xff6969,
						description=f'i do not have permission to create threads in {channel.mention}\nplease correct this and try again\nthis requires the `Create Posts` permission'))
					return False
				if not channel.permissions_for(self.guild.me).manage_messages:
					await interaction.response.send_message(ephemeral=True,embed=Embed(title='error!',color=0xff6969,
						description=f'i do not have permission to pin threads in {channel.mention}\nplease correct this and try again\nthis requires the `Manage Messages` permission'))
					return False
			case 'tts'|'logging'|'talking_stick':
				if channel.type.name not in ['text']:
					await interaction.response.send_message(ephemeral=True,embed=Embed(title='error!',color=0xff6969,
					description=f'channel type `{channel.type.name}` not supported for channel.type.name `{self.category}`'))
					return False
		return True

	async def write_config(self,value,interaction:Interaction) -> None:
		match f'{self.category}.{self.selected}':
			case 'general.embed_color': 
				value = value.replace('#','')
				self.embed.color = int(value,16)
			case 'general.max_roll':
				value = int(value)
				if not (16384 > value > 2): raise ValueError('max_roll must be between 2 and 16384')
			case 'auto_responses.cooldown'|'dad_bot.cooldown': value = int(value)
			case 'general.moderator_role': pass
			case 'logging.enabled' if value and interaction is not None:
				if channels:=[channel.mention for channel in self.guild.channels if not (channel.permissions_for(self.guild.me).view_channel or isinstance(channel,CategoryChannel))]:
					if len(channels) > 100:
						channels = channels[:100]
						channels.append('...')
					create_task(interaction.followup.send(embed=Embed(
						title='WARNING: i can\'t see into the following channels,\nthey will not be logged',
						description='\n'.join(channels),color=0xffff69),ephemeral=True))
			case 'tts.max_message_length':
				value = int(value)
				if not (60 > value > 0): raise ValueError('max_message_length must be between 0 and 60')
		await self.client.db.guild(self.guild.id).config.write(value,[self.category,self.selected])
		await self.client.log.info(f'{self.user.name} set guild config {self.category}/{self.selected} to {value} in {self.guild.name}',**{
			'author':self.user.id,
			'guild':self.guild.id,
			f'{self.category}/{self.selected}':value})
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
		self.embed.title = 'guild config'
		self.embed.description = None
		self.embed.clear_fields()
		self.clear_items()
		if self.back_view is not None: self.add_item(self.back_button)
		self.add_item(self.category_select)
		await interaction.response.edit_message(view=self,embed=self.embed)

	@string_select(
		placeholder='select a config category',
		custom_id='category_select',row=0)
	async def category_select(self,select:Select,interaction:Interaction) -> None:
		self.category = select.values[0]
		self.clear_items()
		self.add_items(self.back_button,self.option_select)
		match self.category:
			case 'auto_responses': self.add_items(self.custom_au_button,self.disable_au_button)
			case 'tts': self.add_item(self.tts_banning_button)
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
				case 'channel': self.add_item(self.channel_select)
				case 'role': self.add_item(self.role_select)
				case _: raise
			options = select.options.copy()
			for option in options: option.default = option.label == self.selected
			select.options = options
		else:
			self.selected = None
			self.reload_embed()
			self.add_items(self.back_button,self.option_select)
			for option in select.options: option.default = False
			match self.category:
				case 'auto_responses': self.add_items(self.custom_au_button,self.disable_au_button)
				case 'tts': self.add_item(self.tts_banning_button)
		await interaction.response.edit_message(view=self,embed=self.embed)

	@channel_select(
		placeholder='select a channel',
		custom_id='channel_select',row=1,min_values=0)
	async def channel_select(self,select:Select,interaction:Interaction) -> None:
		if not select.values:
			await self.write_config(None,interaction)
			await interaction.response.edit_message(embed=self.embed,view=self)
			return
		channel = select.values[0]
		if not await self.validate_channel(channel,interaction): return None
		await self.write_config(channel.id,interaction)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@role_select(
		placeholder='select a role',
		custom_id='role_select',row=1,min_values=0)
	async def role_select(self,select:Select,interaction:Interaction) -> None:
		await self.write_config(select.values[0].id if select.values else None,interaction)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='enable',style=3,
		custom_id='enable_button',row=2)
	async def enable_button(self,button:Button,interaction:Interaction) -> None:
		match self.config_type:
			case 'ewbd': await self.write_config('enabled',interaction)
			case 'bool': await self.write_config(True,interaction)
			case _     : raise
		self.remove_item(self.configure_list_button)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='whitelist',style=1,
		custom_id='whitelist_button',row=2)
	async def whitelist_button(self,button:Button,interaction:Interaction) -> None:
		if self.get_item('configure_list_button') is None: self.add_item(self.configure_list_button)
		self.get_item('configure_list_button').label = f'configure whitelist'
		await self.write_config('whitelist',interaction)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='blacklist',style=1,
		custom_id='blacklist_button',row=2)
	async def blacklist_button(self,button:Button,interaction:Interaction) -> None:
		if self.get_item('configure_list_button') is None: self.add_item(self.configure_list_button)
		self.get_item('configure_list_button').label = f'configure blacklist'
		await self.write_config('blacklist',interaction)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='disable',style=4,
		custom_id='disable_button',row=2)
	async def disable_button(self,button:Button,interaction:Interaction) -> None:
		match self.config_type:
			case 'ewbd': await self.write_config('disabled',interaction)
			case 'bool': await self.write_config(False,interaction)
			case _     : raise
		self.remove_item(self.configure_list_button)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='set',style=1,
		custom_id='modal_button',row=2)
	async def modal_button(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(self,f'set {self.selected}',
			[InputText(label=self.selected,**config_info.get('guild',{}).get(self.category,{}).get(self.selected,{}).get('kwargs',{}))])
		await interaction.response.send_modal(modal)
		await modal.wait()
		await self.write_config(modal.children[0].value,interaction)
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='reset to default',style=4,
		custom_id='reset_button',row=3)
	async def reset_button(self,button:Button,interaction:Interaction) -> None:
		await self.write_config(config_info.get('guild',{}).get(self.category,{}).get(self.selected,{}).get('default',None),interaction)
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='configure',style=1,row=3,
		custom_id='configure_list_button')
	async def configure_list_button(self,button:Button,interaction:Interaction) -> None:
		mode = self.config.get(self.selected,None)
		path = self.selected if (self.category,self.selected) == ('general','hide_commands') else self.category
		embed = Embed(
			title=f'configure {path} {mode}',
			description=f'currently {mode}ed:\n'+(
				'\n'.join([f'<#{i}>' for i in await self.client.db.guild(self.guild.id).data.read([path,mode])]) or 'None'),
			color=self.embed.color)
		await interaction.response.edit_message(embed=embed,view=configure_list_view((path,mode),self,self.user,self.guild,self.client,embed))

	@button(
		label='custom auto responses',style=1,row=2,
		custom_id='custom_au_button')
	async def custom_au_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.send_message('due to the /reg/nal 4.0.0 beta, custom auto responses are currently disabled',ephemeral=True)
		return
		embed = Embed(title=f'custom auto responses',color=self.embed.color)
		au = AutoResponses(self.client.db.auto_response(0)._col,{'custom':True,'guild':str(self.guild.id)})
		await au.reload_au()
		await interaction.response.edit_message(embed=embed,view=au_view(self,self.user,self.guild,self.client,embed,au,True))

	@button(
		label='disable auto responses',style=1,row=2,
		custom_id='disable_au_button')
	async def disable_au_button(self,button:Button,interaction:Interaction) -> None:
		embed = Embed(title=f'disable auto responses',color=self.embed.color)
		view = au_disable_view(self,self.user,self.guild,self.client,embed)
		await view.start()
		await interaction.response.edit_message(embed=embed,view=view)

	@button(
		label='ban users',style=1,row=2,
		custom_id='tts_banning_button')
	async def tts_banning_button(self,button:Button,interaction:Interaction) -> None:
		embed = Embed(title=f'tts banning',color=self.embed.color,
			description=f'currently banned:\n'+(
				'\n'.join([f'<@{i}>' for i in await self.client.db.guild(interaction.guild.id).data.tts.banned_users.read()]) or 'None'))
		await interaction.response.edit_message(embed=embed,view=tts_banning_view(self,self.user,self.guild,self.client,embed))