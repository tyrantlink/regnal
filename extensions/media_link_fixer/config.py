from client.config.models import ConfigOption,ConfigSubcategory,OptionType,ConfigAttrs
from client.config.errors import ConfigValidationError
if not 'TYPE_HINT': from client import Client,Config
from discord import Member,ChannelType,ForumChannel
from discord.abc import GuildChannel




def register_config(config:'Config') -> None:
	config.register_option(
		category = 'guild',
		subcategory = 'general',
		option = ConfigOption(
			name = 'replace_media_links',
			type = OptionType.BOOL,
			default = False,
			short_description = 'replace media links',
			description= '''replaces media links with urls that have better discord embed support
											currently websites:
											- twitter (through fxtwitter)
											- instagram (through ddinstagram)
											- tiktok (through tiktokez)
									 '''.replace('\t','')[:-2]))
