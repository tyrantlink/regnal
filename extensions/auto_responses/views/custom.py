from discord import Member, Embed, Interaction, ButtonStyle, SelectOption, InputTextStyle
from discord.ui import string_select, Select, button, Button, InputText
from utils.pycord_classes import SubView, MasterView, CustomModal
from utils.db.documents.auto_response import AutoResponse
from utils.db.documents.ext.enums import AutoResponseType
from ..embed import au_info_embed, auto_response_404
from .editor import AutoResponseEditorView


class CustomAutoResponseView(SubView):
    def __init__(self, master: MasterView, user: Member) -> None:
        super().__init__(master)
        self.user = user
        self.au: list[AutoResponse]
        self.selected: AutoResponse | None = None

    async def __ainit__(self) -> None:
        await self.reload_au()
        await self.reload_items()
        await self.reload_embed()

    async def __on_back__(self) -> None:
        await self.client.api.internal.reload_au()
        await self.reload_au()
        await self.reload_items()
        await self.reload_embed()

    async def reload_au(self) -> None:
        self.au = [
            au for au in
            self.client.au.au.custom(self.user.guild.id)
            if au.type != AutoResponseType.deleted
        ]

    async def reload_items(self) -> None:
        self.clear_items()
        self.add_items(
            self.back_button,
            self.select_auto_response,
            self.button_import_script,
            self.button_new,
            self.button_search_by_id,
            self.button_search_by_message
        )

        if not self.au:
            self.get_item('select_auto_response').disabled = True

            self.get_item('select_auto_response'
                          ).placeholder = 'no auto responses found!'

            self.get_item('select_auto_response').options = [
                SelectOption(
                    label='no auto responses found!',
                    description='create a new auto response!',
                    value='none')
            ]

            return

        self.get_item('select_auto_response').disabled = False

        self.get_item('select_auto_response'
                      ).placeholder = 'select an auto response'

        self.get_item('select_auto_response').options = [
            SelectOption(
                label=au.trigger if len(
                    au.trigger) < 50 else f'{au.trigger[:50]}...',
                description=au.response[:50] if len(
                    au.response) < 50 else f'{au.response[:50]}...',
                value=au.id
            ) for au in self.au
        ]

        if self.selected is not None:
            self.add_items(
                self.button_edit,
                self.button_delete
            )

    async def reload_embed(self) -> None:
        if self.selected is None:
            self.embed = Embed(
                title='custom auto responses',
                color=self.master.embed_color
            )

            return

        self.embed = await au_info_embed(self.selected, self.client, self.master.embed_color, True)

    @string_select(
        row=0,
        custom_id='select_auto_response')
    async def select_auto_response(self, select: Select, interaction: Interaction) -> None:
        self.selected = self.client.au.get(select.values[0])

        await self.reload_items()
        await self.reload_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='new',
        style=ButtonStyle.green,
        row=2,
        custom_id='button_new')
    async def button_new(self, button: Button, interaction: Interaction) -> None:
        view = self.master.create_subview(
            AutoResponseEditorView, self.user, None
        )

        await view.__ainit__()

        await interaction.response.edit_message(embed=view.embed, view=view)

    @button(
        label='import script',
        style=ButtonStyle.blurple,
        row=2,
        custom_id='button_import_script')
    async def button_import_script(self, button: Button, interaction: Interaction) -> None:
        modal = CustomModal(
            title='import a scripted auto response',
            children=[
                InputText(
                    label='auto response id',
                    custom_id='auto_response_id',
                    placeholder='auto response id')]
        )

        await interaction.response.send_modal(modal)

        await modal.wait()

        au_id = modal.children[0].value

        if not au_id.startswith('s') or self.client.au.get(au_id) is None:
            await self.client.helpers.send_error(
                modal.interaction,
                f'you can find scripts to import [here](<{self.client.project.config.scripted_auto_response_repo}>)',
                'invalid scripted auto response id'
            )
            return

        guild_doc = await self.client.db.guild(self.user.guild.id)

        guild_doc.data.auto_responses.imported_scripts = list(
            set(guild_doc.data.auto_responses.imported_scripts + [au_id])
        )

        await guild_doc.save_changes()

        await self.reload_au()
        await self.reload_items()
        await self.reload_embed()

        await modal.interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='🔎 by id',
        style=ButtonStyle.blurple,
        row=3,
        custom_id='button_search_by_id')
    async def button_search_by_id(self, button: Button, interaction: Interaction) -> None:
        modal = CustomModal(
            title='find an auto response',
            children=[
                InputText(
                    label='auto response id',
                    min_length=2,
                    max_length=6,
                    custom_id='au_id')]
        )

        await interaction.response.send_modal(modal)

        await modal.wait()

        au_id = modal.children[0].value

        if au_id not in {au.id for au in self.au}:
            await modal.interaction.response.send_message(embed=auto_response_404, ephemeral=True)
            return

        self.selected = self.client.au.get(au_id)

        await self.reload_items()
        await self.reload_embed()

        await modal.interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='🔎 by message',
        style=ButtonStyle.blurple,
        row=3,
        custom_id='button_search_by_message')
    async def button_search_by_message(self, button: Button, interaction: Interaction) -> None:
        modal = CustomModal(
            title='find an auto response',
            children=[
                InputText(
                    label='message content',
                    style=InputTextStyle.long,
                    min_length=1,
                    max_length=256,
                    custom_id='message_content'),
                InputText(
                    label='index (when multiple found)',
                    min_length=1,
                    max_length=3,
                    value='0',
                    custom_id='index')]
        )

        await interaction.response.send_modal(modal)

        await modal.wait()

        message_content = modal.children[0].value
        index = int(modal.children[1].value)
        options = self.client.au.match(message_content, pool=self.au)

        if not options:
            await modal.interaction.response.send_message(embed=auto_response_404, ephemeral=True)
            return

        if index >= len(options):
            index = 0

        self.selected = options[index]

        await self.reload_items()
        await self.reload_embed()

        await modal.interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='edit',
        style=ButtonStyle.blurple,
        row=2,
        custom_id='button_edit')
    async def button_edit(self, button: Button, interaction: Interaction) -> None:
        view = self.master.create_subview(
            AutoResponseEditorView, self.user, self.selected
        )

        await view.__ainit__()

        await interaction.response.edit_message(embed=view.embed, view=view)

    @button(
        label='delete',
        style=ButtonStyle.red,
        row=2,
        custom_id='button_delete')
    async def button_delete(self, button: Button, interaction: Interaction) -> None:
        modal = CustomModal(
            title='are you sure?',
            children=[
                InputText(
                    label='type "delete" to confirm',
                    custom_id='confirm_delete',
                    placeholder='type "delete" to confirm')]
        )

        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.children[0].value.lower() != 'delete':
            await modal.interaction.response.defer()
            return

        au_id = self.selected.id
        await self.client.au.delete(au_id)

        self.selected = None

        await self.reload_au()
        await self.reload_items()
        await self.reload_embed()

        await modal.interaction.response.edit_message(embed=self.embed, view=self)

        await interaction.followup.send(
            f'successfully deleted auto response {au_id}!',
            ephemeral=True
        )
