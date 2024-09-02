from client.config.models import ConfigOption, ConfigSubcategory, OptionType, ConfigAttrs, NewConfigSubcategory, NewConfigOption
from client.config.errors import ConfigValidationError
from discord import Member, ChannelType, ForumChannel
from discord.abc import GuildChannel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


async def validate_channel(
    client: 'Client',
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
        ('manage_webhooks', 'i don\'t have permission to manage webhooks in that channel (requires `Manage Webhooks`)')
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
            name='modmail',
            description='modmail options'
        )
    )
]

options = [
    NewConfigOption(
        'guild',
        'modmail',
        ConfigOption(
            name='enabled',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable modmail',
            description='''
                let users report messages to staff with the modmail report message command
            '''.replace('    ', '').strip())
    ),
    NewConfigOption(
        'guild',
        'modmail',
        ConfigOption(
            name='channel',
            type=OptionType.CHANNEL,
            default=None,
            attrs=ConfigAttrs(validation=validate_channel),
            nullable=True,
            short_description='channel where modmail messages are sent',
            description='''
                channel where modmail messages are sent
                channel *must* be a forum channel with no required tags
            '''.replace('    ', '').strip())
    ),
    NewConfigOption(
        'guild',
        'modmail',
        ConfigOption(
            name='allow_anonymous',
            type=OptionType.BOOL,
            default='09:00',
            short_description='allow anonymous modmail messages',
            description='allow anonymous modmail messages')
    )
]
