from .models import ConfigData,ConfigOption,ConfigSubcategory
if not 'TYPE_HINT': from client import Client

class Config:
	def __init__(self,client:'Client') -> None:
		self.client = client
		self.data = ConfigData()

	def register_option(self,category:str,subcategory:str,option:ConfigOption,register_permission:bool=True) -> None:
		if any((option.name == o.name for o in self.data[category][subcategory].options)):
			raise ValueError(f'option with name `{option.name}` already registered in subcategory `{subcategory}`')
		self.data[category][subcategory].options.append(option)
		self.client.log.debug(f'registered config option {category}.{subcategory}.{option.name}')
		if not (category == 'guild' and register_permission): return

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