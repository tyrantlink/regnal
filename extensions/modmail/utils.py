from discord import User, Member, Embed
from utils.db.documents import ModMail
from client import Client
from time import time


async def new_modmail_message(
    client: Client,
    modmail_id: str,
    author: User | Member | None,
    content: str,
    attachments: list[str] | None = None,
    timestamp: int = None
) -> None:
    attachments = attachments or []

    modmail = await client.db.modmail(modmail_id)

    modmail.messages.append(
        ModMail.ModMailMessage(
            author=author.id if author else None,
            content=content,
            attachments=attachments,
            timestamp=timestamp or int(time()))
    )

    await modmail.save_changes()

    if author is None or modmail.anonymous:
        return

    op_id = modmail.messages[0].author

    if author and author.id == op_id:
        return

    if op_id is None:
        return

    op = await client.get_or_fetch_user(op_id)

    if op is None or not op.can_send():
        return

    embed = Embed(
        title=f'new modmail message in {modmail.title}',
        description=client.helpers.handle_cmd_ref(
            'check it with {cmd_ref[modmail]}')
    )

    embed.set_footer(text=f'modmail id: {modmail.modmail_id}')

    await op.send(embed=embed)
