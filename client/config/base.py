from .validation import user_general_no_track,guild_general_embed_color,guild_general_timezone
from .models import ConfigSubcategory,ConfigOption,OptionType,ConfigAttrs
from utils.db.documents.ext.enums import TWBFMode
if not 'TYPE_HINT': from . import Config


def register_user_config(config:'Config') -> None:
	config.register_subcategory('user',ConfigSubcategory(
		name='general',description='general options'))

	config.register_option('user','general',ConfigOption(
		name='no_track',type=OptionType.BOOL,default=False,
		attrs=ConfigAttrs(validation=user_general_no_track),
		short_description='disables tracking',
		description= '''disables the following features:
										  - message counting
										    - counting number of messages sent, used for server leaderboard and active roles
										  - auto response tracking
										    - prevents auto responses from being "found"
										    - auto responses will still be triggered
										    - since they are not found, you will not be able to trigger them with --au <id> or --alt <alt_id>
										NOTE: some data, like api usage will still be tracked'''.replace('\t','')))
	config.register_option('user','general',ConfigOption(
		name='hide_commands',type=OptionType.BOOL,default=True,
		short_description='hide commands you run',
		description= '''whether or not all commands are sent ehpemerally (only you can see them)
										NOTE: sensitive commands, like, /config, /auto_responses, and /get_data are always ephemeral'''.replace('\t','')))

def register_guild_config(config:'Config') -> None:
	config.register_subcategory('guild',ConfigSubcategory(
		name='general',description='general options'))

	config.register_option('guild','general',ConfigOption(
		name='hide_commands',type=OptionType.TWBF,default=TWBFMode.false,
		short_description='force-hide commands',
		description= '''whether or not to ignore user config and force hide commands\n
										- true: commands are force hidden in all channels
										- whitelist: commands are force hidden in specified channels
										- blacklist: commands are force hidden except in specified channels
										- false: fall back to user config'''.replace('\t','')))
	config.register_option('guild','general',ConfigOption(
		name='embed_color',type=OptionType.STRING,default='#69ff69',
		attrs=ConfigAttrs(max_length=7,min_length=6,placeholder='#ffffff',regex=r'^#?[0-9a-fA-F]{6}$',validation=guild_general_embed_color),
		short_description='color of embeds',
		description= '''color of embeds sent by the bot
										does not apply to logs'''.replace('\t','')))
	config.register_option('guild','general',ConfigOption(
		name='timezone',type=OptionType.STRING,default='America/Los_Angeles',
		attrs=ConfigAttrs(max_length=32,min_length=2,placeholder='America/Los_Angeles',validation=guild_general_timezone),
		short_description='used for all time-based events',
		description= '''used for all time-based events
										please refer to [this list on wikipedia](<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>) for a list of options'''.replace('\t','')))


def register_config(config:'Config') -> None:
	register_user_config(config)
	register_guild_config(config)