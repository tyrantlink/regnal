from discord import ApplicationContext, Interaction, Message, HTTPException, Forbidden, Embed
from utils.db.documents.ext.enums import TWBFMode
from regex import sub, finditer, UNICODE, sub
from typing import TYPE_CHECKING
from asyncio import sleep

if TYPE_CHECKING:
    from client import Client


class ClientHelpers:
    def __init__(self, client: 'Client') -> None:
        self.client = client
        self._cmd_ref_pattern = r'{cmd_ref\[([ -_\p{L}\p{N}]{1,32})\]}'
        self.commands = {}

    def load_commands(self) -> None:
        self.commands = {
            command.qualified_name: command.qualified_id
            for command in
            self.client.walk_application_commands()
            if (
                command is not None and
                getattr(command, 'qualified_id', None) is not None
            )
        }

    async def embed_color(self, guild_id: int = None) -> int:
        if guild_id is None:
            return int('69ff69', 16)

        return int((await self.client.db.guild(guild_id)).config.general.embed_color, 16)

    async def ephemeral(self, ctx: ApplicationContext | Interaction) -> bool:
        if ctx.guild:
            guild = await self.client.db.guild(ctx.guild_id)
            match guild.config.general.hide_commands:
                case TWBFMode.true: return True
                case TWBFMode.whitelist if ctx.channel_id in guild.data.hide_commands.whitelist: return True
                case TWBFMode.blacklist if ctx.channel_id not in guild.data.hide_commands.blacklist: return True
                case TWBFMode.false: pass

        return (await self.client.db.user(ctx.user.id)).config.general.hide_commands

    def handle_cmd_ref(self, message: str) -> str:
        for match in finditer(pattern=self._cmd_ref_pattern, string=message, flags=UNICODE):
            message = sub(
                pattern=self._cmd_ref_pattern,
                repl=f'</{match.group(1)}:{self.commands.get(match.group(1),"command not found")}>',
                string=message,
                count=1,
                flags=UNICODE
            )

        return message

    async def notify_reaction(
        self,
        message: Message,
        reaction: str = '❌',
        delay: int | float = 1
    ) -> None:
        try:
            await message.add_reaction(reaction)
            await sleep(delay)
            await message.remove_reaction(reaction, self.client.user)
        except (HTTPException, Forbidden):
            pass

    async def send_error(
        self,
        ctx: ApplicationContext | Interaction,
        description: str | None = None,
        title: str | None = None
    ) -> None:
        await ctx.respond(
            embed=Embed(
                title=title or 'error!',
                description=description,
                color=0xff6969),
            ephemeral=True)
