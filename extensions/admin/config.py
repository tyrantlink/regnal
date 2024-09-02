from client.config.models import ConfigOption, OptionType, NewConfigOption


options = [
    NewConfigOption(
        'guild',
        'general',
        ConfigOption(
            name='moderator_role',
            type=OptionType.ROLE,
            default=None,
            short_description='moderator role',
            description='role that will be pinged for emergency situations (e.g. anti scam bot protection)'
        )
    ),
    NewConfigOption(
        'guild',
        'general',
        ConfigOption(
            name='anti_scam_bot',
            type=OptionType.BOOL,
            default=False,
            short_description='enable anti scam',
            description='''
                detects if a user sends the same message in 3 separate channels within 15 seconds
                if detected
                - their messages will be deleted
                - they will be timed out for 10 minutes
                - a warning will be sent to the configured logging channel that pings the moderator role, with buttons to ban and untimeout the user

                note: i plan to make the options such number of channels and timeframe configurable in the future, but for now this feature is in a testing phase
            '''.replace('    ', '').strip())
    )
]
