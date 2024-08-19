from discord import ButtonStyle, Interaction, Member, Embed
from discord.errors import Forbidden, HTTPException
from utils.pycord_classes import View
from discord.ui import Button, button
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


class AntiScamBotView(View):
    PERMISSION_ERRORS = {
        'ban_user': 'You do not have permission to ban users through the bot!',
        'untimeout_user': 'You do not have permission to untimeout users through the bot!'
    }

    def __init__(self, client: 'Client', hide_timeout: bool = False) -> None:
        super().__init__(timeout=None)
        self.client = client
        self.confirmed = False
        self.add_items(self.button_ban_user)
        if not hide_timeout:
            self.add_items(self.button_untimeout_user)

    async def _base_interaction(self, permission: str, interaction: Interaction) -> Member | None:
        if not await self.client.permissions.check(permission, interaction.user, interaction.guild):
            await interaction.response.send_message(
                self.PERMISSION_ERRORS.get(
                    permission, 'You do not have permission to perform this action!'),
                ephemeral=True
            )
            return None

        user_id = int(interaction.message.embeds[0].footer.text)

        try:
            user = (
                interaction.guild.get_member(user_id) or
                await interaction.guild.fetch_member(user_id)
            )
        except (Forbidden, HTTPException):
            await interaction.response.send_message(
                'Failed to find user! Are they still in the server?',
                ephemeral=True
            )
            return None

        return user

    @button(
        label='ban user',
        style=ButtonStyle.red,
        custom_id='button_ban_user')
    async def button_ban_user(self, button: Button, interaction: Interaction) -> None:
        user = await self._base_interaction('admin.ban_user', interaction)

        if user is None:
            return

        if not self.confirmed:
            self.confirmed = True
            self.button_ban_user.label = 'confirm ban'
            await interaction.response.edit_message(view=self)
            return

        await user.ban(reason='anti scam bot protection')

        embed = Embed(
            description=f'{user.mention} has been banned',
            color=0xff6969
        )
        embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.avatar.url
        )

        self.disable_all_items()

        await interaction.response.edit_message(view=self)

        await interaction.followup.send(
            embed=embed
        )

    @button(
        label='untimeout user',
        style=ButtonStyle.green,
        custom_id='button_untimeout_user')
    async def button_untimeout_user(self, button: Button, interaction: Interaction) -> None:
        user = await self._base_interaction('admin.untimeout_user', interaction)

        if user is None:
            return

        await user.remove_timeout(reason='anti scam bot protection')

        embed = Embed(
            description=f'{user.mention} has been untimeouted',
            color=0x69ff69
        )
        embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.avatar.url
        )

        self.disable_all_items()

        await interaction.response.edit_message(view=self)

        await interaction.followup.send(
            embed=embed
        )
