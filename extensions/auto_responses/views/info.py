from utils.db.documents import AutoResponse, User as UserDoc, Guild as GuildDoc
from discord import User, Embed, Member, Interaction, ButtonStyle
from utils.db.documents.ext.enums import AutoResponseMethod
from utils.pycord_classes import View
from discord.ui import button, Button
from ..embed import au_info_embed
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


class AutoResponseInfoView(View):
    def __init__(
        self,
        client: 'Client',
        user: Member,
        auto_response: AutoResponse
    ) -> None:
        super().__init__(timeout=None)
        self.client = client
        self.user = user
        self.original_au = auto_response
        self.au = auto_response
        self.embed: Embed
        self.guild_overrides: dict = {}
        self.with_overrides: bool = False
        self.has_guild_permissions: bool = False

    async def __ainit__(self) -> None:
        if getattr(self.user, 'guild', None) is None:
            raise ValueError('AutoResponseInfoView must be used in a guild!')

        user_doc = await self.client.db.user(self.user.id)

        self.has_guild_permissions = (
            getattr(self.user, 'guild', None) is not None and
            await self.client.permissions.check(
                'auto_responses.override',
                self.user,
                self.user.guild)
        )

        guild_doc = await self.client.db.guild(self.user.guild.id)

        self.guild_overrides = \
            guild_doc.data.auto_responses.overrides.get(
                self.au.id, {}
            )

        await self.reload_embed(user_doc)
        await self.reload_buttons(user_doc)

    async def reload_embed(self, user_doc: UserDoc | None = None) -> None:
        user_doc = user_doc or await self.client.db.user(self.user.id)

        self.embed = await au_info_embed(
            auto_response=self.au,
            client=self.client,
            embed_color=await self.client.helpers.embed_color(
                self.user.guild.id
                if getattr(self.user, 'guild', None)
                else None
            ),
            extra_info=user_doc.config.general.developer_mode
        )

        if self.guild_overrides:
            self.embed.set_author(
                name=f'!! this server has custom overrides !!'
            )

    async def reload_buttons(self, user_doc: UserDoc | None = None, guild_doc: GuildDoc | None = None) -> None:
        self.clear_items()

        if self.embed.title == 'this auto response has been deleted':
            return

        user_doc = user_doc or await self.client.db.user(self.user.id)

        self.add_item(
            self.button_enable
            if self.au.id in user_doc.data.auto_responses.disabled else
            self.button_disable
        )

        if not self.has_guild_permissions:
            return

        guild_doc = guild_doc or await self.client.db.guild(self.user.guild.id)

        match guild_doc.data.auto_responses.overrides.get(self.au.id, {}).get('method', None):
            case AutoResponseMethod.disabled.value: self.add_item(self.button_enable_server)
            case _: self.add_item(self.button_disable_server)

        if self.guild_overrides:
            self.add_item(self.button_with_overrides)
            self.get_item('button_with_overrides').style = (
                ButtonStyle.green
                if self.with_overrides else
                ButtonStyle.red
            )

    @button(
        label='enable',
        style=ButtonStyle.green,
        custom_id='button_enable')
    async def button_enable(self, button: Button, interaction: Interaction) -> None:
        user_doc = await self.client.db.user(self.user.id)

        try:
            user_doc.data.auto_responses.disabled.remove(self.au.id)
        except ValueError:
            pass

        await user_doc.save_changes()
        await self.reload_buttons(user_doc)

        await interaction.response.edit_message(view=self)

    @button(
        label='disable',
        style=ButtonStyle.red,
        custom_id='button_disable')
    async def button_disable(self, button: Button, interaction: Interaction) -> None:
        user_doc = await self.client.db.user(self.user.id)
        user_doc.data.auto_responses.disabled.append(self.au.id)

        await user_doc.save_changes()
        await self.reload_buttons(user_doc)

        await interaction.response.edit_message(view=self)

    @button(
        label='enable (server-wide)',
        style=ButtonStyle.green,
        custom_id='button_enable_server')
    async def button_enable_server(self, button: Button, interaction: Interaction) -> None:
        user_doc = await self.client.db.user(self.user.id)
        guild_doc = await self.client.db.guild(self.user.guild.id)

        if self.au.id not in guild_doc.data.auto_responses.overrides:
            guild_doc.data.auto_responses.overrides[self.au.id] = {}

        guild_doc.data.auto_responses.overrides[self.au.id].pop('method', None)

        await guild_doc.save_changes()
        await self.reload_buttons(user_doc, guild_doc)

        await interaction.response.edit_message(view=self)

    @button(
        label='disable (server-wide)',
        style=ButtonStyle.red,
        custom_id='button_disable_server')
    async def button_disable_server(self, button: Button, interaction: Interaction) -> None:
        user_doc = await self.client.db.user(self.user.id)
        guild_doc = await self.client.db.guild(self.user.guild.id)

        if self.au.id not in guild_doc.data.auto_responses.overrides:
            guild_doc.data.auto_responses.overrides[self.au.id] = {}

        guild_doc.data.auto_responses.overrides[self.au.id]['method'] = AutoResponseMethod.disabled

        await guild_doc.save_changes()
        await self.reload_buttons(user_doc, guild_doc)

        await interaction.response.edit_message(view=self)

    @button(
        row=1,
        label='with overrides',
        style=ButtonStyle.red,
        custom_id='button_with_overrides')
    async def button_with_overrides(self, button: Button, interaction: Interaction) -> None:
        self.with_overrides = not self.with_overrides

        self.au = (
            self.au.with_overrides(self.guild_overrides)
            if self.with_overrides else
            self.original_au
        )

        await self.reload_buttons()
        await self.reload_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)
