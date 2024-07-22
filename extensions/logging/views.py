from discord import ButtonStyle, Interaction, Message
from utils.pycord_classes import View
from discord.ui import Button, button
from typing import TYPE_CHECKING
from time import time

if TYPE_CHECKING:
    from client import Client


class BaseLogView(View):
    def __init__(self, client: 'Client') -> None:
        super().__init__()
        self.client = client
        self.add_item(self.button_clear)

    async def _clear_message(self, message: Message, user: str, timestamp: str, include_view: bool = True) -> None:
        embed = message.embeds[0]
        embed.clear_fields()

        if message.reference is None:
            embed.add_field(
                name=f'CLEARED {timestamp}',
                value=f'logs cleared by {user}'
            )

            message.embeds = [embed]
            await message.edit(embed=embed, view=self if include_view else None)

            return

        embed.description = f'logs cleared by {user} at {timestamp}'
        message.embeds = [embed]

        if include_view:
            self.get_item('button_clear').disabled = True

        await message.edit(embed=embed, view=self if include_view else None)

        reference = (
            message.reference.cached_message or
            await message.channel.fetch_message(message.reference.message_id)
        )

        await self._clear_message(
            message=reference,
            user=user,
            timestamp=timestamp,
            include_view=False
        )

    @button(
        label='clear', custom_id='button_clear',
        style=ButtonStyle.red)
    async def button_clear(self, button: Button, interaction: Interaction) -> None:
        if not await self.client.permissions.check('logging.clear_logs', interaction.user, interaction.guild):
            await interaction.response.send_message(
                'You do not have permission to clear logs!',
                ephemeral=True)
            return

        await self._clear_message(
            message=interaction.message,
            user=interaction.user.mention,
            timestamp=f'<t:{int(time())}:t>'
        )

        await interaction.response.defer()


class EditedLogView(BaseLogView):
    ...


class DeletedLogView(BaseLogView):
    def __init__(self, client: 'Client', has_attachments: bool = True) -> None:
        super().__init__(client)

        if has_attachments:
            self.add_item(self.button_hide_attachments)

    @button(
        label='hide attachments', custom_id='button_hide_attachments',
        style=ButtonStyle.red)
    async def button_hide_attachments(self, button: Button, interaction: Interaction) -> None:
        if not await self.client.permissions.check('logging.hide_attachments', interaction.user, interaction.guild):
            await interaction.response.send_message(
                'You do not have permission to hide attachments!',
                ephemeral=True
            )
            return

        embed = interaction.message.embeds[0]
        embed.fields[-1].value = f'attachments hidden by {interaction.user.mention}'
        interaction.message.embeds[0] = embed

        button.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)


class BulkDeletedLogView(BaseLogView):
    ...
