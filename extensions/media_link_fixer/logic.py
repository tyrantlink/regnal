from .subcog import ExtensionMediaLinkFixerSubCog
from .classes import MediaFixer
from discord import Message
from regex import findall


fixers = [
    MediaFixer(r'(twitter|x)\.com', 'fxtwitter.com'),
    MediaFixer(r'instagram\.com', 'ddinstagram.com', wait_time=7),
    MediaFixer(r'tiktok\.com', 'tnktok.com', wait_time=10),
    MediaFixer(r'pixiv\.net', 'phixiv.net', wait_time=10),
]


class ExtensionMediaLinkFixerLogic(ExtensionMediaLinkFixerSubCog):
    def find_fixes(self, content: str) -> list[MediaFixer]:
        fixes = []

        for fix in fixers:
            if fix.only_if_includes and fix.only_if_includes not in content:
                continue

            if findall(f'(?<!<)https:\/\/(.*\.)?{fix.find}', content):
                fixes.append(fix)

        return fixes

    async def wait_for_good_bot(self, message: Message) -> None:
        try:
            response: Message = await self.client.wait_for(
                'message',
                check=lambda m: all((
                    'good bot' in m.content.lower(),
                    m.channel == message.channel
                )),
                timeout=60
            )
        except TimeoutError:
            return

        await response.reply(
            '<:cutesmile:1118502809772494899>',
            mention_author=False
        )