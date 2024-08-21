from ..models import ConfigCategory, ConfigSubcategory, OptionType
from discord import Interaction, SelectOption, User, Member, Embed
from utils.pycord_classes import SubView, MasterView
from .additional_view import AdditionalViewButton
from discord.ui import string_select, Select
from .option import ConfigOptionView
from typing import Any


class ConfigSubcategoryView(SubView):
    def __init__(
        self,
        master: 'MasterView',
        config_category: ConfigCategory,
        config_subcategory: ConfigSubcategory,
        user: User | Member,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        self.config_category = config_category
        self.config_subcategory = config_subcategory
        self.user = user
        self.generate_embed()

    async def __ainit__(self) -> None:
        self.add_item(self.back_button)
        self.add_item(self.option_select)

        match self.config_category.name:
            case 'user': current_config = getattr((await self.client.db.user(self.user.id)).config, self.config_subcategory.name)
            case 'guild': current_config = getattr((await self.client.db.guild(self.user.guild.id)).config, self.config_subcategory.name)

        user_permissions = await self.client.permissions.user(self.user, self.user.guild)
        for view in self.config_subcategory.additional_views:
            view_button = AdditionalViewButton(self, view)
            self.add_item(view_button)

            if view.required_permissions is not None:
                match self.config_category.name:
                    case 'user':
                        pass
                    case 'guild' if (
                        await self.client.permissions.check(view.required_permissions, self.user, self.user.guild)
                    ):
                        pass
                    case 'guild' if (
                        self.config_subcategory.name in user_permissions
                    ):
                        self.get_item(view_button.custom_id).disabled = True
                    case _:
                        continue

        options = []

        for option in self.config_subcategory.options:
            read_only = True

            match self.config_category.name:
                case 'user':
                    read_only = False
                case 'guild' if (
                    await self.client.permissions.check(
                        f'{self.config_subcategory.name}.{option.name}',
                        self.user,
                        self.user.guild)
                ):
                    read_only = False
                case 'guild' if (
                    self.config_subcategory.name in user_permissions
                ):
                    pass
                    read_only = False
                case _:
                    continue

            value = getattr(current_config, option.name)

            value = ((
                '\n'.join([
                    self._convert_to_mention(value[0], option.type),
                    f'and {len(value)-1} more' if len(value) > 1 else '']
                    if value else
                    'None'
                )) if option.attrs.multi else
                self._convert_to_mention(value, option.type))

            self.embed.add_field(name=option.name, value=value)

            if read_only:
                continue

            options.append(SelectOption(
                label=option.name,
                description=option.short_description))

        if options:
            self.get_item('option_select').options = options
            return

        self.get_item('option_select').options = [SelectOption(label='None')]
        self.get_item('option_select').placeholder = 'no access'
        self.get_item('option_select').disabled = True

    def _convert_to_mention(self, value: Any, option_type: OptionType) -> str:
        if value not in {'None', None}:
            match option_type:
                case OptionType.CHANNEL: return f'<#{value}>'
                case OptionType.ROLE: return f'<@&{value}>'
                case OptionType.USER: return f'<@{value}>'

        return str(value)

    async def __on_back__(self) -> None:
        self.generate_embed()
        self.clear_items()
        await self.__ainit__()

    def generate_embed(self) -> None:
        self.embed = Embed(
            title=f'{self.config_subcategory.name} config', color=self.master.embed_color)

        match self.config_category.name:
            case 'user':
                self.embed.set_author(
                    name=self.user.display_name,
                    icon_url=self.user.display_avatar.url)
            case 'guild':
                self.embed.set_author(
                    name=self.user.guild.name,
                    icon_url=(
                        self.user.guild.icon.url
                        if self.user.guild.icon else
                        self.user.guild.me.display_avatar.url
                    ))
            case _:
                raise ValueError('improper config category name')

        self.embed.set_footer(
            text=f'config.{self.config_category.name}.{self.config_subcategory.name}')

    @string_select(
        placeholder='select an option',
        custom_id='option_select')
    async def option_select(self, select: Select, interaction: Interaction) -> None:
        option = self.config_subcategory[select.values[0]]
        view = self.master.create_subview(
            ConfigOptionView, self.config_category, self.config_subcategory, option, self.user)
        await view.__ainit__()

        await interaction.response.edit_message(view=view, embed=view.embed)
