from discord.ui import button, InputText, user_select, channel_select, role_select, string_select, Select
from client.config.models import ConfigCategory, ConfigSubcategory, ConfigOption, OptionType
from discord import User, Member, Button, ButtonStyle, Interaction
from utils.pycord_classes import SubView, MasterView, CustomModal
from .type_validators import ConfigOptionTypeValidator
from .configure_channels import ConfigChannelsView
from .type_handlers import ConfigOptionTypeHandler
from utils.db.documents.ext.enums import TWBFMode
from .typehint import ConfigOptionTypeHint
from .logic import ConfigOptionLogic


class ConfigOptionView(
        ConfigOptionLogic,
        ConfigOptionTypeHandler,
        ConfigOptionTypeValidator,
        ConfigOptionTypeHint,
        SubView
):
    def __init__(
        self,
        master: 'MasterView',
        config_category: ConfigCategory,
        config_subcategory: ConfigSubcategory,
        option: ConfigOption,
        user: User | Member,
        **kwargs
    ) -> None:
        SubView.__init__(self, master, **kwargs)
        self.config_category = config_category
        self.config_subcategory = config_subcategory
        self.option = option
        self.user = user
        self.selected_options: set[str | int] = set()

    async def __ainit__(self) -> None:
        match self.config_category.name:
            case 'user': self.object_doc = await self.client.db.user(self.user.id)
            case 'guild': self.object_doc = await self.client.db.guild(self.user.guild.id)
            case _: raise ValueError('improper config category name')

        await self.handle_option()
        await self.generate_embed()

    @button(
        label='reset to default', row=3,
        style=ButtonStyle.red,
        custom_id='button_reset')
    async def button_reset(self, button: Button, interaction: Interaction) -> None:
        await self.write_config(self.option.default, interaction)

    @button(
        label='true', row=2,
        style=ButtonStyle.blurple,
        custom_id='button_true')
    async def button_true(self, button: Button, interaction: Interaction) -> None:
        await self.write_config(True if self.option.type == OptionType.BOOL else TWBFMode.true, interaction)

    @button(
        label='false', row=2,
        style=ButtonStyle.blurple,
        custom_id='button_false')
    async def button_false(self, button: Button, interaction: Interaction) -> None:
        await self.write_config(False if self.option.type == OptionType.BOOL else TWBFMode.false, interaction)

    @button(
        label='whitelist', row=2,
        style=ButtonStyle.blurple,
        custom_id='button_whitelist')
    async def button_whitelist(self, button: Button, interaction: Interaction) -> None:
        await self.write_config(TWBFMode.whitelist, interaction)

    @button(
        label='blacklist', row=2,
        style=ButtonStyle.blurple,
        custom_id='button_blacklist')
    async def button_blacklist(self, button: Button, interaction: Interaction) -> None:
        await self.write_config(TWBFMode.blacklist, interaction)

    @button(
        label='configure channels', row=3,
        style=ButtonStyle.blurple,
        custom_id='button_configure_channels')
    async def button_configure_channels(self, button: Button, interaction: Interaction) -> None:
        view = self.master.create_subview(
            ConfigChannelsView, self.config_category, self.config_subcategory, self.option, self.user)
        await view.__ainit__()
        await interaction.response.edit_message(view=view, embed=view.embed)

    @button(
        label='set', row=2,
        style=ButtonStyle.blurple,
        custom_id='button_set')
    async def button_set(self, button: Button, interaction: Interaction) -> None:
        modal = CustomModal(
            f'set {self.option.name}',
            [InputText(
                label=self.option.name,
                placeholder=self.option.attrs.placeholder,
                max_length=self.option.attrs.max_length,
                min_length=self.option.attrs.min_length,
                custom_id='input_set')])

        await interaction.response.send_modal(modal)

        await modal.wait()
        await self.write_config(modal.children[0].value, modal.interaction)

    @button(
        label='add', row=2,
        style=ButtonStyle.green,
        custom_id='button_add')
    async def button_add(self, button: Button, interaction: Interaction) -> None:
        await self.write_config(
            list(set(self.current_value()) | self.selected_options),
            interaction)

    @button(
        label='remove', row=2,
        style=ButtonStyle.red,
        custom_id='button_remove')
    async def button_remove(self, button: Button, interaction: Interaction) -> None:
        await self.write_config(
            list(set(self.current_value()) - self.selected_options), interaction)

    async def _select(self, select: Select, interaction: Interaction) -> None:
        if self.option.attrs.multi:
            self.selected_options = {val.id for val in select.values}
            await interaction.response.defer()
            return

        await self.write_config(
            select.values if len(
                select.values) > 1 else select.values[0] if select.values else None,
            interaction)

    @channel_select(
        placeholder='select a channel',
        custom_id='select_channel', row=1, min_values=0)
    async def select_channel(self, select: Select, interaction: Interaction) -> None:
        await self._select(select, interaction)

    @role_select(
        placeholder='select a role',
        custom_id='select_role', row=1, min_values=0)
    async def select_role(self, select: Select, interaction: Interaction) -> None:
        await self._select(select, interaction)

    @user_select(
        placeholder='select a user',
        custom_id='select_user', row=1, min_values=0)
    async def select_user(self, select: Select, interaction: Interaction) -> None:
        await self._select(select, interaction)

    @string_select(
        placeholder='select an option',
        custom_id='select_string', row=1)
    async def select_string(self, select: Select, interaction: Interaction) -> None:
        await self._select(select, interaction)
