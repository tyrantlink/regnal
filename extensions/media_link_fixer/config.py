from client.config.models import ConfigOption, OptionType, NewConfigOption


options = [
    NewConfigOption(
        'guild',
        'general',
        ConfigOption(
            name='replace_media_links',
            type=OptionType.BOOL,
            default=False,
            short_description='replace media links',
            description='''
                replaces media links with urls that have better discord embed support
                currently websites:
                - twitter/x (through [fxtwitter](<https://github.com/FixTweet/FxTwitter>)
                - instagram (through [ddinstagram](<https://github.com/Wikidepia/InstaFix>))
                - tiktok (through [tnktok](<https://github.com/okdargy/fxtiktok>))
                - pixiv (through [phixiv](<https://github.com/thelaao/phixiv>))
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'user',
        'general',
        ConfigOption(
            name='disable_media_link_replacement',
            type=OptionType.BOOL,
            default=False,
            short_description='disable media link replacement',
            description='''
                media link replacement is a feature that replaces social media links with urls that have better discord embed support
                - if enabled, media links will not be replaced with their respective embed friendly urls
                - only effective if the server has media link replacement enabled
            '''.replace('    ', '').strip()
        )
    )
]
