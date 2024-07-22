from client.config.models import ConfigOption, OptionType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Config


def register_config(config: 'Config') -> None:
    config.register_option(
        category='guild',
        subcategory='general',
        option=ConfigOption(
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
            '''.replace('    ', '').strip())
    )

    config.register_option(
        category='user',
        subcategory='general',
        option=ConfigOption(
            name='disable_media_link_replacement',
            type=OptionType.BOOL,
            default=False,
            short_description='disable media link replacement',
            description='''
                if enabled, media links will not be replaced with their respective embed friendly urls
                only effective if the server has media link replacement enabled
                media link replacement is a feature that replaces social media links with urls that have better discord embed support
                (e.g. twitter, instagram, tiktok, pixiv -> fxtwitter, ddinstagram, tnktok, phixiv)
            '''.replace('    ', '').strip())
    )
