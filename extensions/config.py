from discord.ui import View,Button,Select,button,Modal,InputText,Item
from discord import SelectOption,Interaction,Embed,ApplicationContext
from discord.commands import slash_command
from discord.ext.commands import Cog
from utils.tyrantlib import perm
from main import client_cls,config
from asyncio import sleep

class input_text(Modal):
	def __init__(self,embed:Embed,view:View,label:str,placeholder:str,max_length:int) -> None:
		self.label = label
		self.embed = embed
		self.view = view
		super().__init__(title='set value')
		self.add_item(InputText(label=label,placeholder=placeholder,max_length=max_length))

	async def callback(self,interaction:Interaction) -> None:
		self.response = self.children[0].value
		for index,field in enumerate(self.embed.fields):
			if field.name.split(':')[0] == self.label:
				if self.label == 'embed_color':
					self.embed.set_field_at(index,name=f'{self.label}: #{self.response.upper()}',value=field.value)
					try: self.embed.color = int(self.response,16)
					except ValueError: pass
				else: self.embed.set_field_at(index,name=f'{self.label}: {self.response}',value=field.value)
		await interaction.response.edit_message(embed=self.embed,view=self.view)
		self.stop()

class options_dropdown(Select):
	def __init__(self,view:View) -> None:
		self.v = view
		super().__init__(placeholder='select an option',options=[SelectOption(label=k) for k,v in config[self.v.current_menu].items()])
	
	async def callback(self,interaction:Interaction) -> None:
		for i in [self.v.button_true,self.v.button_false,self.v.button_input]:
			if i in self.v.children: self.v.remove_item(i)
		self.v.selected = self.values[0]
		self.v.embed.description = f'selected: {self.v.selected}'
		match config[self.v.current_menu][self.v.selected]['type']:
			case 'bool':
				self.v.add_item(self.v.button_true)
				self.v.add_item(self.v.button_false)
			case 'input':
				self.v.add_item(self.v.button_input)
			case _: await self.v.client.log.debug('unknown config type in base_config_menu callback')
		await self.v.update_self(self.v)
		await interaction.response.edit_message(embed=self.v.embed,view=self.v)

class view(View):
	def __init__(self,*,client:client_cls,allowed_config:list,embed:Embed,embed_color:int) -> None:
		super().__init__()
		self.clear_items()
		self.client = client
		self.allowed_config = allowed_config
		self.embed = embed
		self.embed_color = embed_color
		self.config_type = None
		if 'user' in self.allowed_config: self.add_item(self.button_user)
		if 'guild' in self.allowed_config: self.add_item(self.button_guild)
		if 'logging' in self.allowed_config: self.add_item(self.button_logging)
		if '/reg/nal' in self.allowed_config: self.add_item(self.button_regnal)

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)
	
	async def update_self(self,new_self:View) -> None:
		self = new_self

	async def reload_embed(self,interaction:Interaction) -> None:
		match self.current_menu:
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
		match self.current_menu:
			case 'user': await self.client.db.users.write(interaction.user.id,['config',self.selected],value)
			case 'guild': await self.client.db.guilds.write(interaction.guild.id,['config',self.selected],value)
			case 'logging': await self.client.db.guilds.write(interaction.guild.id,['log_config',self.selected],value)
			case '/reg/nal': await self.client.db.inf.write('/reg/nal',['config',self.selected],value)
			case _: await self.client.log.debug('unknown menu in modify_config callback')
		await self.client.log.debug(f'[CONFIG] [{self.current_menu.upper()}] {interaction.user} set {self.selected} to {value}')
		if not from_modal:
			self.embed.clear_fields()
			await self.reload_embed(interaction)
			await interaction.response.edit_message(embed=self.embed,view=self)
	
	async def validate_input(self,value:str) -> int:
		match self.current_menu:
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
		self.current_menu = option
		self.config_type = option
		self.embed.title = f'{option} config'
		self.embed.description = None
		self.embed.clear_fields()
		await self.reload_embed(interaction)
		self.clear_items()
		self.add_item(options_dropdown(self))
		self.add_item(self.button_back)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(label='<',style=2)
	async def button_back(self,button:Button,interaction:Interaction) -> None:
		self.embed.clear_fields()
		self.embed.title = 'config options'
		self.embed.description = 'please select a config category'
		self.clear_items()
		if 'user' in self.allowed_config: self.add_item(self.button_user)
		if 'guild' in self.allowed_config: self.add_item(self.button_guild)
		if 'logging' in self.allowed_config: self.add_item(self.button_logging)
		if '/reg/nal' in self.allowed_config: self.add_item(self.button_regnal)

		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(label='set to True',style=3)
	async def button_true(self,button:Button,interaction:Interaction) -> None:
		await self.modify_config(True,interaction)

	@button(label='set to False',style=4)
	async def button_false(self,button:Button,interaction:Interaction) -> None:
		await self.modify_config(False,interaction)
	
	@button(label='set',style=3)
	async def button_input(self,button:Button,interaction:Interaction) -> None:
		modal = input_text(self.embed,self,label=self.selected,placeholder=config[self.current_menu][self.selected]['default'],max_length=config[self.current_menu][self.selected]['max_length'])
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

class config_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

	@slash_command(
		name='config',
		description='set config')
	async def slash_config(self,ctx:ApplicationContext) -> None:
		allowed_config = ['user']
		if await perm('manage_guild',ctx):
			allowed_config.append('guild')
			if await perm('view_audit_log',ctx): allowed_config.append('logging')
		if await perm('bot_owner',ctx): allowed_config.append('/reg/nal')
		embed_color = await self.client.embed_color(ctx)
		embed = Embed(title='config options',description='please select a config category',color=embed_color)
		await ctx.response.send_message(embed=embed,view=view(
			client=self.client,
			allowed_config=allowed_config,
			embed=embed,
			embed_color=embed_color),
			ephemeral=True)

def setup(client:client_cls) -> None: client.add_cog(config_cog(client))