from client.config.models import ConfigOption,ConfigSubcategory,OptionType,ConfigAttrs
if not 'TYPE_HINT': from client import Client,Config
from discord import Member,CategoryChannel


async def validate_channel_visibility(client:'Client',option:ConfigOption,value:bool,user:Member) -> tuple[bool,str|None]:
	if not value: return value,None
	channels = [
		channel.mention for channel in user.guild.channels if not (
			channel.permissions_for(user.guild.me).view_channel or isinstance(channel,CategoryChannel))]
	if not channels: return value,None
	if len(channels) > 100:
		channels = channels[:100]
		channels.append('...')
	return value,f'i can\'t see into the following channels,\nthey will not be logged\n\n'+'\n'.join(channels)

def register_config(config:'Config') -> None:
	config.register_subcategory(
		category = 'guild',
		subcategory = ConfigSubcategory(
			name = 'logging',
			description = 'logging options'))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'enabled',
			type = OptionType.BOOL,
			default = False,
			attrs = ConfigAttrs(
				validation = validate_channel_visibility),
			short_description = 'enable/disable logging',
			description= '''enable/disable logging\n
											if disabled, all logging will be disabled
											if enabled you can view logs on https://logs.regn.al
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'channel',
			type = OptionType.CHANNEL,
			default = None,
			short_description = 'channel used for some logging',
			description= '''channel used for some logging
											full logs still visible on https://logs.regn.al
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'log_bots',
			type = OptionType.BOOL,
			default = False,
			short_description = 'enable/disable logging of bot messages',
			description= '''enable/disable logging of bot and webhook messages
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'log_commands',
			type = OptionType.BOOL,
			default = True,
			short_description = 'enable/disable logging of command usage',
			description= '''enable/disable logging of command usage
											\*note, only applies to commands *directly* related to the server
											e.g. {cmd_ref[config]} changes, qotd custom question, etc
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'deleted_messages',
			type = OptionType.BOOL,
			default = True,
			short_description = 'enable/disable logging of deleted messages',
			description= '''enable/disable logging of deleted messages
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'edited_messages',
			type = OptionType.BOOL,
			default = True,
			short_description = 'enable/disable logging of edited messages',
			description= '''enable/disable logging of edited messages
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'member_join',
			type = OptionType.BOOL,
			default = False,
			short_description = 'enable/disable logging of member joins',
			description= '''enable/disable logging of member joins
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'member_leave',
			type = OptionType.BOOL,
			default = False,
			short_description = 'enable/disable logging of member leaves',
			description= '''enable/disable logging of member leaves
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'member_ban',
			type = OptionType.BOOL,
			default = True,
			short_description = 'enable/disable logging of member bans',
			description= '''enable/disable logging of member bans
									 '''.replace('\t','')[:-2]))

	config.register_option(
		category = 'guild',
		subcategory = 'logging',
		option = ConfigOption(
			name = 'member_unban',
			type = OptionType.BOOL,
			default = True,
			short_description = 'enable/disable logging of member unbans',
			description= '''enable/disable logging of member unbans
									 '''.replace('\t','')[:-2]))