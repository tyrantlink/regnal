from client.config.models import ConfigOption, ConfigSubcategory, OptionType, ConfigAttrs
from discord import Member, TextChannel, ChannelType, Role
from client.config.errors import ConfigValidationError
from discord.abc import GuildChannel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client, Config


async def validate_channel(
    client: 'Client',
    option: ConfigOption,
    value: TextChannel | GuildChannel,
    user: Member
) -> tuple[TextChannel, str | None]:
    if value.type != ChannelType.text:
        raise ConfigValidationError('channel must be a text channel!')

    return value, (
        None
        if value.can_send()
        else 'i can\'t send messages in that channel, config still saved, but please correct this!'
    )


async def validate_role(
    client: 'Client',
    option: ConfigOption,
    value: Role,
    user: Member
) -> tuple[Role, str | None]:
    if not value.is_assignable():
        raise ConfigValidationError('''
            i can\'t assign that role!
	        please make sure i have the manage roles permission and that the role is below my highest role
            '''.replace('    ', '').strip()
        )
    return value, None


def register_config(config: 'Config') -> None:
    config.register_subcategory(
        category='guild',
        subcategory=ConfigSubcategory(
            name='talking_stick',
            description='talking stick options')
    )

    config.register_option(
        category='guild',
        subcategory='talking_stick',
        option=ConfigOption(
            name='enabled',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable talking stick',
            description='''
                daily random roll to give an active user a specific role\n
                intended to give users send_messages permissions in a channel, but can be used for anything
            '''.replace('    ', '').strip())
    )

    config.register_option(
        category='guild',
        subcategory='talking_stick',
        option=ConfigOption(
            name='channel',
            type=OptionType.CHANNEL,
            default=None,
            attrs=ConfigAttrs(
                validation=validate_channel),
            short_description='channel used to announce the talking stick',
            description='channel used to announce the talking stick')
    )

    config.register_option(
        category='guild',
        subcategory='talking_stick',
        option=ConfigOption(
            name='role',
            type=OptionType.ROLE,
            default=None,
            attrs=ConfigAttrs(
                validation=validate_role),
            short_description='role given to the user',
            description='role given to the user')
    )

    config.register_option(
        category='guild',
        subcategory='talking_stick',
        option=ConfigOption(
            name='limit',
            type=OptionType.ROLE,
            default=None,
            short_description='role that limits who can get the talking stick',
            description='''
                role that limits who can get the talking stick\n
                if not set, all users can get the talking stick
            '''.replace('    ', '').strip())
    )

    config.register_option(
        category='guild',
        subcategory='talking_stick',
        option=ConfigOption(
            name='time',
            type=OptionType.STRING,
            default='09:00',
            attrs=ConfigAttrs(
                min_length=5,
                max_length=5,
                regex=r'^\d{2}:\d{2}$'),
            short_description='time of day talking stick is announced',
            description='''
                time of day talking stick is announced
                format: HH:MM (24 hour) (includes leading zeros)
                follows guild set timezone
            '''.replace('    ', '').strip())
    )

    config.register_option(
        category='guild',
        subcategory='talking_stick',
        option=ConfigOption(
            name='announcement_message',
            type=OptionType.STRING,
            default='congrats {user} you have the talking stick.',
            attrs=ConfigAttrs(
                max_length=200),
            short_description='message sent when a user gets the talking stick',
            description='''
                message sent when a user gets the talking stick\n
                format: {user} is replaced with the user's mention
            '''.replace('    ', '').strip())
    )
