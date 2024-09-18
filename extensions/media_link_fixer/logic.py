from .subcog import ExtensionMediaLinkFixerSubCog
from .classes import MediaFixer
from regex import finditer, sub
from discord import Message


FIXERS = [
    MediaFixer(r'(twitter|x)\.com', 'fxtwitter.com'),
    MediaFixer(r'instagram\.com', 'ddinstagram.com', wait_time=7),
    MediaFixer(r'tiktok\.com', 'tnktok.com', wait_time=10),
    MediaFixer(r'pixiv\.net', 'phixiv.net', wait_time=10),
]


class ExtensionMediaLinkFixerLogic(ExtensionMediaLinkFixerSubCog):
    def fix(self, content: str) -> tuple[str | None, set[MediaFixer]]:
        out_message = ['links converted to embed friendly urls:']
        fixers_used = set()

        # ? this is a stupid way of doing this, but i'm very tired
        offset = 0
        spoilers = []

        for start, end in [m.span() for m in finditer(r'\|\|.+?\|\|', content)]:
            start += offset
            end += offset
            content = f'{content[:start]}{content[start+2:end-2]}{content[end:]}'
            offset -= 4
            spoilers.append((start, end-4))
        

        for fix in FIXERS:
            if fix.only_if_includes and fix.only_if_includes not in content:
                continue
            
            # ? intentionally don't replace if the link is suppressed by <>
            for match in finditer(f'(\s|^)(?<!<)https:\/\/(.*\.)?{fix.find}\S+', content):
                link = content[match.start():match.end()].strip()

                if fix.remove_params:
                    link = link.split('?')[0]

                link = sub(fix.find, fix.replace, link)

                for spoiler in spoilers:
                    # ? start+1 because i'm technically matching the space before the link
                    if spoiler[0] <= match.start()+1 and spoiler[1] >= match.end():
                        link = f'||{link}||'
                        break

                out_message.append(link)
                fixers_used.add(fix)

        return '\n'.join(out_message) if len(out_message) > 1 else None, fixers_used

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
        guild_doc = await self.client.db.guild(message.guild.id)
        guild_doc.data.statistics.good_bots += 1
        await guild_doc.save_changes()
