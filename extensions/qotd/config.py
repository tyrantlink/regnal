from __future__ import annotations
from client.config.models import ConfigOption, ConfigSubcategory, OptionType, ConfigAttrs, NewConfigSubcategory, NewConfigOption
from client.config.errors import ConfigValidationError
from discord import Member, ChannelType, ForumChannel
from discord.abc import GuildChannel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


async def validate_channel(
    client: Client,
    option: ConfigOption,
    value: ForumChannel | GuildChannel,
    user: Member
) -> tuple[ForumChannel, str | None]:
    if value.type != ChannelType.forum:
        raise ConfigValidationError('channel must be a forum channel!')

    permissions = value.permissions_for(user.guild.me)
    missing_permissions = []

    for perm, description in (
            ('send_messages', 'i don\'t have permission to send messages in that channel (requires `Send Messages`)'),
            ('embed_links', 'i don\'t have permission to embed links in that channel (requires `Embed Links`)'),
            ('create_public_threads',
             'i don\'t have permission to create threads in that channel (requires `Create Posts`)'),
            ('manage_threads', 'i don\'t have permission to manage threads in that channel (requires `Manage Posts`)'),
            ('manage_messages', 'i don\'t have permission to pin messages in that channel (requires `Manage Messages`)')
    ):
        if not getattr(permissions, perm):
            missing_permissions.append(description)

    if missing_permissions:
        raise ConfigValidationError(
            'permissions error!\ni need the following permissions in that channel:\n' +
            '\n'.join(missing_permissions)
        )

    return value, None


subcategories = [
    NewConfigSubcategory(
        'guild',
        ConfigSubcategory(
            name='qotd',
            description='question of the day options'
        )
    )
]


options = [
    NewConfigOption(
        'guild',
        'qotd',
        ConfigOption(
            name='enabled',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable qotd',
            description='''
                random daily questions\n
                let members suggest custom questions with {cmd_ref[qotd custom]}
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'qotd',
        ConfigOption(
            name='channel',
            type=OptionType.CHANNEL,
            default=None,
            attrs=ConfigAttrs(
                validation=validate_channel),
            nullable=True,
            short_description='channel where qotd is sent',
            description='''
                channel where qotd is sent
                channel **must** be a forum channel with no required tags
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'qotd',
        ConfigOption(
            name='time',
            type=OptionType.STRING,
            default='09:00',
            attrs=ConfigAttrs(
                min_length=5,
                max_length=5,
                regex=r'^\d{2}:\d{2}$'),
            short_description='time of day qotd is asked',
            description='''
                time of day qotd is asked
                format: HH:MM (24 hour) (includes leading zeros)
                follows guild set timezone
            '''.replace('    ', '').strip()
        )
    )
]
