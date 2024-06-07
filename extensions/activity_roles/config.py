from client.config.models import ConfigOption,ConfigSubcategory,OptionType,ConfigAttrs,AdditionalView
from client.config.errors import ConfigValidationError
if not 'TYPE_HINT': from client import Client,Config
from .views import ActivityRolesIgnoreView
from discord import Member,Role


async def validate_role(
	client:'Client',
	option:ConfigOption,
	value:Role,
	user:Member
) -> tuple[Role,str|None]:
	if not value.is_assignable(): raise ConfigValidationError('''i can\'t assign that role!
	please make sure i have the manage roles permission and that the role is below my highest role'''.replace('\t',''))
	return value,None

def register_config(config:'Config') -> None:
	config.register_subcategory(
		category = 'guild',
		subcategory = ConfigSubcategory(
			name = 'activity_roles',
			description = 'activity role options',
			additional_views=[
				AdditionalView(
					required_permissions = 'activity_roles.ignore',
					button_label = 'ignore roles',
					button_row = 2,
					button_id = 'ignore_roles',
					view = ActivityRolesIgnoreView)]))

	config.register_option(
		category = 'guild',
		subcategory = 'activity_roles',
		option = ConfigOption(
			name = 'enabled',
			type = OptionType.BOOL,
			default = False,
			short_description = 'enable/disable activity roles',
			description ='''give your most active members a role'''.replace('\t','')))

	config.register_option(
		category = 'guild',
		subcategory = 'activity_roles',
		option = ConfigOption(
			name = 'role',
			type = OptionType.ROLE,
			default = None,
			attrs = ConfigAttrs(validation = validate_role),
			nullable=True,
			short_description = 'role given to active users',
			description ='''role given to active users'''.replace('\t','')))
	
	config.register_option(
		category = 'guild',
		subcategory = 'activity_roles',
		option = ConfigOption(
			name = 'timeframe',
			type = OptionType.INT,
			default = 7,
			attrs=ConfigAttrs(min_value=1,max_value=30),
			short_description = 'number of days counted for activity',
			description ='''number of days counted for activity
											(e.g. last 7 days)'''.replace('\t','')))
	
	config.register_option(
		category = 'guild',
		subcategory = 'activity_roles',
		option = ConfigOption(
			name = 'max_roles',
			type = OptionType.INT,
			default = 10,
			attrs=ConfigAttrs(min_value=1,max_value=50),
			short_description = 'maximum number of roles to give',
			description ='''maximum number of roles to give
											(e.g. the 10 most active members get a role)'''.replace('\t','')))
	
	if 'logging' in {s.name for s in config.data.guild.subcategories}:
		#? this doesn't actually work because the logging extensions is always loaded after this one
		#? will require a full rework of the config system to fix
		config.register_option(
			category = 'guild',
			subcategory = 'logging',
			option = ConfigOption(
				name = 'activity_roles',
				type = OptionType.BOOL,
				default = True,
				short_description = 'enable/disable logging of activity role changes',
				description= '''enable/disable logging of activity role changes
										'''.replace('\t','')[:-2]))
