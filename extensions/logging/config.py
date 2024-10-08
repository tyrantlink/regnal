from __future__ import annotations
from client.config.models import ConfigOption, ConfigSubcategory, OptionType, ConfigAttrs, NewConfigSubcategory, NewConfigOption
from discord import Member, CategoryChannel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


async def validate_channel_visibility(
        client: Client,
        option: ConfigOption,
        value: bool,
        user: Member
) -> tuple[bool, str | None]:
    if not value:
        return value, None

    channels = [
        channel.mention
        for channel in user.guild.channels
        if not (
            channel.permissions_for(user.guild.me).view_channel or
            isinstance(channel, CategoryChannel)
        )
    ]

    if not channels:
        return value, None

    if len(channels) > 100:
        channels = channels[:100]
        channels.append('...')

    return (
        value,
        value, f'i can\'t see into the following channels,\nthey will not be logged\n\n' +
        '\n'.join(channels)
    )

subcategories = [
    NewConfigSubcategory(
        'guild',
        ConfigSubcategory(
            name='logging',
            description='logging options'
        )
    )
]

options = [
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='enabled',
            type=OptionType.BOOL,
            default=False,
            attrs=ConfigAttrs(
                validation=validate_channel_visibility),
            short_description='enable/disable logging',
            description='''
                enable/disable logging\n
                if disabled, all logging will be disabled
                if enabled you can view logs on https://logs.regn.al
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='channel',
            type=OptionType.CHANNEL,
            default=None,
            nullable=True,
            short_description='channel used for some logging',
            description='''
                channel used for some logging
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='log_bots',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable logging of bot messages',
            description='''
                enable/disable logging of bot and webhook messages
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='log_commands',
            type=OptionType.BOOL,
            default=True,
            short_description='enable/disable logging of command usage',
            description='''
                enable/disable logging of command usage
                \*note, only applies to commands *directly* related to the server
                e.g. {cmd_ref[config]} changes, qotd custom question, etc
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='deleted_messages',
            type=OptionType.BOOL,
            default=True,
            short_description='enable/disable logging of deleted messages',
            description='enable/disable logging of deleted messages'
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='edited_messages',
            type=OptionType.BOOL,
            default=True,
            short_description='enable/disable logging of edited messages',
            description='enable/disable logging of edited messages'
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='member_join',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable logging of member joins',
            description='enable/disable logging of member joins'
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='member_leave',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable logging of member leaves',
            description='enable/disable logging of member leaves'
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='member_ban',
            type=OptionType.BOOL,
            default=True,
            short_description='enable/disable logging of member bans',
            description='enable/disable logging of member bans'
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='member_unban',
            type=OptionType.BOOL,
            default=True,
            short_description='enable/disable logging of member unbans',
            description='enable/disable logging of member unbans'
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='pluralkit_support',
            type=OptionType.BOOL,
            default=False,
            short_description='suppress messages deleted by pluralkit',
            description='''
                suppress messages deleted by pluralkit
                warning: this will add a delay to deleted message logs, as it requires waiting for the pluralkit api
                it probably won't catch all messages, as the api can sometimes go down, but it should catch most
                do not use unless you have <@466378653216014359> (pluralkit) in your server.
            '''.replace('    ', '').strip()
        )
    )
]
