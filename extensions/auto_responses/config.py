if not 'TYPE_HINT': from client.config import Config
from client.config.models import ConfigOption,ConfigSubcategory,OptionType,AdditionalView,ConfigAttrs
from .views.custom import CustomAutoResponseView
from .views.overrides import AutoResponseOverridesView
from utils.db.documents.ext.enums import TWBFMode,AUCooldownMode




def register_config(config:'Config') -> None:
	config.register_option('user','general',ConfigOption(
		name='auto_responses',type=OptionType.BOOL,default=True,
		short_description='configure auto responses',
		description= '''enable auto responses in chat'''.replace('\t','')))
	
	config.register_subcategory('guild',ConfigSubcategory(
		name='auto_responses',description='auto response options',
		additional_views=[
			AdditionalView(
				button_label='custom auto responses',
				button_row=0,
				button_id='custom_auto_responses',
				view=CustomAutoResponseView),
			AdditionalView(
				button_label='override auto responses',
				button_row=0,
				button_id='override_auto_responses',
				view=AutoResponseOverridesView)]))
	
	config.register_option('guild','auto_responses',ConfigOption(
		name='enabled',type=OptionType.TWBF,default=TWBFMode.true,
		short_description='enable/disable auto responses',
		description= '''automatic responses to certain words or phrases, can be disabled individually, or entirely, by users or guilds\n
										- true: auto responses are enabled in all channels
										- whitelist: auto responses are enabled in specified channels
										- blacklist: auto responses are enabled except in specified channels
										- false: all auto responses are disabled'''.replace('\t','')))
	config.register_option('guild','auto_responses',ConfigOption(
		name='cooldown',type=OptionType.INT,default=0,
		attrs=ConfigAttrs(min_value=0,max_value=86400),
		short_description='configure cooldown',
		description= '''time (in seconds) after sending an auto response where another one will not be sent'''.replace('\t','')))
	config.register_option('guild','auto_responses',ConfigOption(
		name='cooldown_mode',type=OptionType.STRING,default=AUCooldownMode.none.name,
		attrs=ConfigAttrs(options=[
			('none','ignore cooldown'),
			('user','cooldown per user'),
			('channel','cooldown per channel'),
			('guild','cooldown applies to all channels')]),
		short_description='configure cooldown mode',
		description= '''cooldown mode for auto responses\n
										- none: ignore cooldown
										- user: cooldown per user
										- channel: cooldown per channel
										- guild: cooldown applies to all channels'''.replace('\t','')))
	config.register_option('guild','auto_responses',ConfigOption(
		name='allow_cross_guild_responses',type=OptionType.BOOL,default=False,
		short_description='usage of auto responses from other servers',
		description= '''allow custom auto responses from other guilds to be used (using the --au argument)
										very, very dangerous permission, allows users to send arbitrary auto responses
										use at your own risk.'''.replace('\t','')))
	
	