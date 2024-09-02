from __future__ import annotations
from client.config.models import ConfigOption, ConfigSubcategory, OptionType, ConfigAttrs, ConfigStringOption, AdditionalView, NewConfigSubcategory, NewConfigOption
from client.config.errors import ConfigValidationError
from utils.db.documents.ext.enums import TTSMode
from discord import Member, ChannelType
from .valid_voices import valid_voices
from .views import TTSBanningView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


async def validate_voice(
    client: Client,
    option: ConfigOption,
    value: str,
    user: Member
) -> tuple[str, str | None]:
    value = value.strip().replace(' ', '')

    if value not in valid_voices.value:
        raise ConfigValidationError(f'invalid voice `{value}`')

    return value, None


async def validate_channels(
        client: Client,
        option: ConfigOption,
        value: list[int],
        user: Member
) -> tuple[int, str | None]:
    warnings = []

    for channel_id in value:
        channel = user.guild.get_channel(channel_id)
        if channel.type != ChannelType.text:
            raise ConfigValidationError('channel must be a text channel')

        if not channel.permissions_for(channel.guild.me).read_messages:
            warnings.append(
                f'i cannot read messages in channel, please correct this'
            )

    return value, '\n'.join(warnings) if warnings else None


subcategories = [
    NewConfigSubcategory(
        'user',
        ConfigSubcategory(
            name='tts',
            description='text-to-speech options'
        )
    ),
    NewConfigSubcategory(
        'guild',
        ConfigSubcategory(
            name='tts',
            description='text-to-speech options',
            additional_views=[
                AdditionalView(
                    required_permissions='tts.ban',
                    button_label='ban users',
                    button_row=2,
                    button_id='tts_ban',
                    view=TTSBanningView
                )
            ]
        )
    )
]

options = [
    NewConfigOption(
        'user',
        'tts',
        ConfigOption(
            name='mode',
            type=OptionType.STRING,
            default=TTSMode.only_when_muted.name,
            attrs=ConfigAttrs(
                enum=TTSMode,
                options=[
                    ConfigStringOption(
                        'only when muted',
                        'speak message only when you\'re muted',
                        TTSMode.only_when_muted.name),
                    ConfigStringOption(
                        'always',
                        'speak every message',
                        TTSMode.always.name),
                    ConfigStringOption(
                        'never',
                        'never speak messages',
                        TTSMode.never.name)]),
            short_description='tts mode',
            description='''
                when to use tts
                - only when muted: speak message only when you're muted
                - always: speak every message
                - never: never speak messages
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'user',
        'tts',
        ConfigOption(
            name='name',
            type=OptionType.STRING,
            default=None,
            short_description='tts name',
            nullable=True,
            attrs=ConfigAttrs(
                min_length=1,
                max_length=32),
            description='''
                voice name to use for tts
                - if not set, your display name will be used
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'user',
        'tts',
        ConfigOption(
            name='auto_join',
            type=OptionType.BOOL,
            default=False,
            short_description='auto join tts channel',
            description='''
                join tts channel when you send a message
                - you must be in a voice channel
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'user',
        'tts',
        ConfigOption(
            name='voice',
            type=OptionType.STRING,
            default=None,
            attrs=ConfigAttrs(
                min_length=1,
                max_length=32,
                validation=validate_voice),
            short_description='tts voice',
            nullable=True,
            description='''
                voice to use for tts
                - you can find and test voice [here](https://cloud.google.com/text-to-speech#demo)
                - the voice is the option in the "Voice Name" section
                  - e.g. "en-US-Neural2-H" or "de-DE-Neural2-D"
                - there is a tradeoff between quality and speed
                - this is a rough map of voice quality and response time:
                  - studio  : 1400ms
                  - journey : 600ms
                  - polyglot: 275ms
                  - neural2 : 250ms
                  - casual  : 250ms
                  - standard: 100ms
                  - wavenet : 100ms
                  - news    : 80ms
                - if set to None, the current server's default voice will be used
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'user',
        'tts',
        ConfigOption(
            name='speaking_rate',
            type=OptionType.FLOAT,
            default=1.0,
            attrs=ConfigAttrs(
                min_value=0.25,
                max_value=1.5),
            short_description='speaking rate',
            description='''
                speaking rate for tts
                - 0.25 to 2.0
                - 0.25 is 25% of normal speed
                - 1.0 is normal speed
                - 1.5 is 1.5x normal speed
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'user',
        'tts',
        ConfigOption(
            name='text_correction',
            type=OptionType.BOOL,
            default=True,
            short_description='text correction',
            description='silently corrects text so it\'s more accurately pronounced'
        )
    ),
    NewConfigOption(
        'user',
        'tts',
        ConfigOption(
            name='read_filenames',
            type=OptionType.BOOL,
            default=False,
            short_description='read filenames',
            description='''
                read filenames when tts is enabled
                (e.g. "USER sent crab.png" versus "USER sent an image")
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'tts',
        ConfigOption(
            name='enabled',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable tts',
            description='enable/disable tts'
        )
    ),
    NewConfigOption(
        'guild',
        'tts',
        ConfigOption(
            name='channels',
            type=OptionType.CHANNEL,
            default=[],
            attrs=ConfigAttrs(
                multi=True,
                max_value=25,
                validation=validate_channels),
            short_description='configure tts channels',
            description='''
                configure tts channels
                users will be able to send tts messages from all these channels *in addition to* the current voice channel
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'tts',
        ConfigOption(
            name='default_voice',
            type=OptionType.STRING,
            default=None,
            attrs=ConfigAttrs(
                validation=validate_voice),
            short_description='default tts voice',
            nullable=True,
            description='''
                default voice to use for tts
                - if set to None, en-US-Neural2-H will be used
            '''.replace('    ', '').strip()
        )
    )

]
