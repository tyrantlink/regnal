from discord.ui import View,Button,button,Item
from discord import Interaction,Embed
from .selects import config_select
from .modals import config_modal
from main import client_cls
from .shared import config


class config_view(View):
	def __init__(self,*,client:client_cls,allowed_config:list,embed:Embed,embed_color:int) -> None:
		super().__init__()
		self.clear_items()
		self.client = client
		self.allowed_config = allowed_config
		self.embed = embed
		self.embed_color = embed_color
		self.config_type = None
		self.menu_history = []
		if 'user' in self.allowed_config: self.add_item(self.button_user)
		if 'guild' in self.allowed_config: self.add_item(self.button_guild)
		if 'logging' in self.allowed_config: self.add_item(self.button_logging)
		if '/reg/nal' in self.allowed_config: self.add_item(self.button_regnal)

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)
	
	async def _no_track_enabled(self,interaction:Interaction) -> None:
		await self.client.db.users.write(interaction.user.id,['messages'],None)
		for guild in interaction.user.mutual_guilds:
			await self.client.db.guilds.unset(guild.id,['leaderboards','messages',str(interaction.user.id)])
			await self.client.db.guilds.unset(guild.id,['leaderboards','sticks',str(interaction.user.id)])
	
	async def update_self(self,new_self:View) -> None:
		self = new_self

	async def reload_embed(self,interaction:Interaction) -> None:
		match self.menu_history[-1]:
			case 'user':
				for k,v in (await self.client.db.users.read(interaction.user.id,['config'])).items():
					self.embed.add_field(name=f'{k}: {v}',value=config[self.current_menu][k]['description'])
			case 'guild':
				for k,v in (await self.client.db.guilds.read(interaction.guild.id,['config'])).items():
					self.embed.add_field(name=f'{k}: {v if k != "embed_color" else "#" + hex(v)[2:].upper()}',value=config[self.current_menu][k]['description'])
			case 'logging':
				for k,v in (await self.client.db.guilds.read(interaction.guild.id,['log_config'])).items():
					if k in ['log_channel']: continue
					self.embed.add_field(name=f'{k}: {v}',value=config[self.current_menu][k]['description'])
			case '/reg/nal':
				for k,v in (await self.client.db.inf.read('/reg/nal',['config'])).items():
					self.embed.add_field(name=f'{k}: {v}',value=config[self.current_menu][k]['description'])
	
	async def modify_config(self,value:bool|str|int,interaction:Interaction,from_modal:bool=False) -> None:
		match self.menu_history[-1]:
			case 'user': await self.client.db.users.write(interaction.user.id,['config',self.selected],value)
			case 'guild': await self.client.db.guilds.write(interaction.guild.id,['config',self.selected],value)
			case 'logging': await self.client.db.guilds.write(interaction.guild.id,['log_config',self.selected],value)
			case '/reg/nal': await self.client.db.inf.write('/reg/nal',['config',self.selected],value)
			case _: await self.client.log.debug('unknown menu in modify_config callback')
		if self.selected == 'no_track':
			if value: await self._no_track_enabled(interaction)
			else: await self.client.db.users.write(interaction.user.id,['messages'],0)
		await self.client.log.debug(f'[CONFIG] {" ".join([f"[{menu.upper()}]" for menu in self.menu_history])} {interaction.user} set {self.selected} to {value}',config={'category':self.current_menu,'option':self.selected,'set_to':value})
		if not from_modal:
			self.embed.clear_fields()
			await self.reload_embed(interaction)
			await interaction.response.edit_message(embed=self.embed,view=self)
	
	async def validate_input(self,value:str) -> int:
		match self.menu_history[-1]:
			case 'user': pass #none used
			case 'guild': 
				match self.selected:
					case 'embed_color':
						value = value[1:] if value.startswith('#') else value
						if len(value) != 6: return
						try: value = int(value,16)
						except ValueError: return
					case 'max_roll':
						try: value = int(value)
						except ValueError: return
						if not (16384 > value > 2): return
			case 'logging': pass # none used
			case '/reg/nal': pass # none used
		return value

	async def base_config_option_button(self,option:str,interaction:Interaction) -> None:
		self.menu_history.append(option)
		self.config_type = option
		self.embed.title = f'{option} config'
		self.embed.description = None
		self.embed.clear_fields()
		await self.reload_embed(interaction)
		self.clear_items()
		self.add_item(config_select(self))
		self.add_item(self.button_back)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(label='<',style=2)
	async def button_back(self,button:Button,interaction:Interaction) -> None:
		self.menu_history.pop()
		self.embed.clear_fields()
		self.embed.title = 'config options'
		self.embed.description = 'please select a config category'
		self.clear_items()
		if 'user' in self.allowed_config: self.add_item(self.button_user)
		if 'guild' in self.allowed_config: self.add_item(self.button_guild)
		if 'logging' in self.allowed_config: self.add_item(self.button_logging)
		if '/reg/nal' in self.allowed_config: self.add_item(self.button_regnal)

		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(label='enable',style=3)
	async def button_enable(self,button:Button,interaction:Interaction) -> None:
		if config.get(self.current_menu,{}).get(interaction.message.embeds[0].description.split(' ')[-1],{}).get('type',None) == 'str':
			await self.modify_config('enabled',interaction)
		else:
			await self.modify_config(True,interaction)

	@button(label='whitelist',style=1)
	async def button_whitelist(self,button:Button,interaction:Interaction) -> None:
		await self.modify_config('whitelist',interaction)

	@button(label='blacklist',style=1)
	async def button_blacklist(self,button:Button,interaction:Interaction) -> None:
		await self.modify_config('blacklist',interaction)

	@button(label='disable',style=4)
	async def button_disable(self,button:Button,interaction:Interaction) -> None:
		if config.get(self.current_menu,{}).get(interaction.message.embeds[0].description.split(' ')[-1],{}).get('type',None) == 'str':
			await self.modify_config('disabled',interaction)
		else:
			await self.modify_config(False,interaction)
	
	@button(label='set',style=3)
	async def button_input(self,button:Button,interaction:Interaction) -> None:
		modal = config_modal(self.embed,self,label=self.selected,placeholder=config[self.current_menu][self.selected]['default'],max_length=config[self.current_menu][self.selected]['max_length'])
		await interaction.response.send_modal(modal)
		await modal.wait()
		value = await self.validate_input(modal.response)
		if value is None: await interaction.response.send_message('invalid input',ephemeral=True)
		else: await self.modify_config(value,interaction,True)
	
	@button(label='user',style=1)
	async def button_user(self,button:Button,interaction:Interaction) -> None:
		await self.base_config_option_button('user',interaction)
		
	@button(label='guild',style=1)
	async def button_guild(self,button:Button,interaction:Interaction) -> None:
		await self.base_config_option_button('guild',interaction)

	@button(label='logging',style=1)
	async def button_logging(self,button:Button,interaction:Interaction) -> None:
		await self.base_config_option_button('logging',interaction)
	
	@button(label='/reg/nal',style=1)
	async def button_regnal(self,button:Button,interaction:Interaction) -> None:
		await self.base_config_option_button('/reg/nal',interaction)
