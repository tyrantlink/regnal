from .models import ConfigData,ConfigOption,ConfigSubcategory
from .base import register_config as register_base_config
from discord import slash_command,ApplicationContext
if not 'TYPE_HINT': from client import Client
from utils.pycord_classes import MasterView
from .views import ConfigHomeView

class Config:
	def __init__(self,client:'Client') -> None:
		self.client = client
		self.data = ConfigData()
		self.client.add_application_command(self.slash_config)
		self._stupid_slash_command_compat()

	def register_option(self,category:str,subcategory:str,option:ConfigOption,register_permission:bool=True) -> None:
		if any((option.name == o.name for o in self.data[category][subcategory].options)):
			raise ValueError(f'option with name `{option.name}` already registered in subcategory `{subcategory}`')
		self.data[category][subcategory].options.append(option)
		self.client.log.debug(f'registered config option {category}.{subcategory}.{option.name}')
		if not (category == 'guild' and register_permission): return
		self.client.permissions.register_permission(f'{subcategory}.{option.name}')

	def unregister_option(self,category:str,subcategory:str,option:str) -> None:
		option_data = next((o for o in self.data[category][subcategory].options if o.name == option),None)
		if option_data is None:
			raise ValueError(f'option with name `{option}` not registered in subcategory `{subcategory}`')
		self.data[category][subcategory].options.remove(option_data)
		self.client.log.debug(f'unregistered config option {category}.{subcategory}.{option}')
		if category != 'guild': return
		self.client.permissions.unregister_permission(f'{subcategory}.{option}')

	def register_subcategory(self,category:str,subcategory:ConfigSubcategory,register_permission:bool=True) -> None:
		if any((subcategory.name == s.name for s in self.data[category].subcategories)):
			raise ValueError(f'subcategory with name `{subcategory.name}` already registered in category `{category}`')
		self.data[category].subcategories.append(subcategory)
		self.client.log.debug(f'registered config subcategory {category}.{subcategory.name}')
		if not (category == 'guild' and register_permission): return
		self.client.permissions.register_permission(subcategory.name)
		self.client.log.debug(f'registered permission {subcategory.name}')

	def unregister_subcategory(self,category:str,subcategory:str) -> None:
		subcategory_data = next((s for s in self.data[category].subcategories if s.name == subcategory),None)
		if subcategory_data is None:
			raise ValueError(f'subcategory with name `{subcategory}` not registered in category `{category}`')
		self.data[category].subcategories.remove(subcategory_data)
		self.client.log.debug(f'unregistered config subcategory {category}.{subcategory}')
		if category != 'guild': return
		self.client.permissions.unregister_permission(subcategory)

	# this is stupid and dumb and garbage and doo doo and awful and dumb. and stupid.
	def _stupid_slash_command_compat(self) -> None:
		self.checks = []
		index = self.client._pending_application_commands.index([c for c in self.client._pending_application_commands if c.name == 'config'][0])
		self.client._pending_application_commands[index].options = []
		self.client._pending_application_commands[index].parent = self
		self.client._pending_application_commands[index].attached_to_group = True

	@slash_command(
		name='config',
		description='set config')
	async def slash_config(self,ctx:ApplicationContext) -> None:
		mv = MasterView(self.client,await self.client.helpers.embed_color(ctx.guild_id))
		view = mv.create_subview(ConfigHomeView,user=ctx.user)
		await view.__ainit__()
		await ctx.response.send_message(embed=view.embed,view=view,ephemeral=True)