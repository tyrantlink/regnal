from client.permissions.views import PermissionManagerView
from pydantic import BaseModel as _BaseModel,Field
from typing import Callable,Any,NamedTuple
from enum import Enum,EnumType


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
	required_permissions:str|None = None
	button_label:str
	# button_style:int set to 1
	button_row:int
	button_id:str
	view:type # uninstantiated utils.atomic_view.SubView subclass

class ConfigStringOption(NamedTuple):
	label:str
	description:str|None
	value:str

class ConfigAttrs(NamedTuple):
	max_length:int|None = None # applicable to str,int,float #? max length of string version of value (enforced in modal)
	min_length:int|None = None # applicable to str,int,float #? min length of string version of value (enforced in modal)
	placeholder:str|None = None # applicable to str,int,float #? placeholder in input modal
	options:list[ConfigStringOption] = [] # applicable to str #? if given, input type will be select
	max_value:int|float|None = None # applicable to int,float,role,user,channel #? max value of value OR max number of options
	min_value:int|float|None = None # applicable to int,float,role,user,channel #? min value of value OR max number of options
	regex:str|None = None # applicable to str #? regex to match value against
	multi:bool = False # applicable to channel,role,user #? adds add/remove buttons, stored value must be list
	enum:Enum|EnumType|None = None # applicable to str #? enum to get int value from
	validation:Callable|None = None # applicable to all #? additional validation function, takes value as argument, returns bool

class ConfigOption(BaseModel):
	class Config:
		arbitrary_types_allowed = True

	name:str
	type:'OptionType'
	short_description:str|None = Field(None,max_length=100)
	description:str|None = None
	default:Any = None
	nullable:bool = False
	attrs:ConfigAttrs = ConfigAttrs()

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
	def __init__(self) -> None:
		self.user = ConfigCategory(name='user')
		self.guild = ConfigCategory(name='guild',
			additional_views=[
				AdditionalView(
					required_permissions='admin.manage_permissions',
					button_label='manage permissions',
					button_row=2,
					button_id='manage_permissions',
					view=PermissionManagerView),
			])
		self.dev = ConfigCategory(name='dev')

	def __getitem__(self,key:str) -> ConfigCategory:
		match key:
			case 'user': return self.user
			case 'guild': return self.guild
			case 'dev': return self.dev
			case _: raise KeyError(f'no category with name `{key}` found.')