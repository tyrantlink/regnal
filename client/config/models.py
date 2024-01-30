from pydantic import BaseModel as _BaseModel,Field
from typing import Optional,Any
from typing import Callable
from enum import Enum


class BaseModel(_BaseModel):
	def __hash__(self):
		return hash((type(self),) + tuple(self.__dict__.values()))

class ConfigCategory(BaseModel):
	name:str
	subcategories:list['ConfigSubcategory']=[]
	additional_views:list['AdditionalView']=[] # put guild permission config here

	def __getitem__(self,key:str) -> 'ConfigSubcategory':
		for subcategory in self.subcategories:
			if subcategory.name == key: return subcategory
		else: raise KeyError(f'no subcategory with name `{key}` found. has it been registered?')

class ConfigSubcategory(BaseModel):
	name:str
	description:str|None = None
	options:list['ConfigOption'] = []
	additional_views:list['AdditionalView'] = []

	def __getitem__(self,key:str) -> 'ConfigSubcategory':
		for option in self.options:
			if option.name == key: return option
		else: raise KeyError(f'no subcategory with name `{key}` found. has it been registered?')

class AdditionalView(BaseModel):
	button_label:str
	# button_style:int set to 1
	button_row:int
	button_id:str
	view:type # uninstantiated utils.atomic_view.SubView subclass

class ConfigOption(BaseModel):
	name:str
	type:'OptionType'
	short_description:str|None = Field(None,max_length=100)
	description:str|None = None
	default:Any = None
	attrs:Optional['ConfigAttrs'] = None

class ConfigAttrs(BaseModel):
	class Config:
		arbitrary_types_allowed = True
	max_length:int|None = None # applicable to str,int,float #? max length of string version of value (enforced in modal)
	min_length:int|None = None # applicable to str,int,float #? min length of string version of value (enforced in modal)
	placeholder:str|None = None # applicable to str,int,float #? placeholder in input modal
	options:list[str|tuple[str,str]]|None = None # applicable to str #? if given, input type will be select, if tuples, first element is label, second is description
	max_value:int|float|None = None # applicable to int,float #? max value of value
	min_value:int|float|None = None # applicable to int,float #? min value of value
	regex:str|None = None # applicable to str #? regex to match value against
	validation:Callable = None # applicable to all #? additional validation function, takes value as argument, returns bool

class OptionType(Enum):
	BOOL = 0 # adds true/false buttons
	TWBF = 1 # adds four buttons: true/whitelist/blacklist/false, and a configure channels button if whitelist/blacklist is selected
	STRING = 2 # text popup modal or string select if attrs.options is given
	INT = 3 # text popup modal, parses to int
	FLOAT = 4 # text popup modal, parses to float
	CHANNEL = 5 # adds channel select
	ROLE = 6 # adds role select
	USER = 7 # adds user select

class ConfigData:
	user = ConfigCategory(name='user')
	guild = ConfigCategory(name='guild')
	dev = ConfigCategory(name='dev')

	def __getitem__(self,key:str) -> ConfigCategory:
		match key:
			case 'user': return self.user
			case 'guild': return self.guild
			case 'dev': return self.dev
			case _: raise KeyError(f'no category with name `{key}` found.')