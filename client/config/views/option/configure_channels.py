from client.config.models import ConfigCategory, ConfigSubcategory, ConfigOption
from discord import User, Member, Embed, Button, ButtonStyle, Interaction
from discord.ui import button, channel_select, Select
from utils.pycord_classes import SubView, MasterView
from discord.abc import GuildChannel


class ConfigChannelsView(SubView):
    def __init__(
        self,
        master: 'MasterView',
        config_category: ConfigCategory,
        config_subcategory: ConfigSubcategory,
        option: ConfigOption,
        user: User | Member,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        self.config_category = config_category
        self.config_subcategory = config_subcategory
        self.option = option
        self.user = user
        self.selected = set()

    async def __ainit__(self) -> None:
        match self.config_category.name:
            case 'user': self.object_doc = await self.client.db.user(self.user.id)
            case 'guild': self.object_doc = await self.client.db.guild(self.user.guild.id)
            case _: raise ValueError('improper config category name')

        self.add_items(
            self.configure_channels_select,
            self.back_button,
            self.configure_channels_add,
            self.configure_channels_remove)

        deleted_channels = set()
        for i in self.get_channel_ids():
            if not self.user.guild.get_channel(i):
                deleted_channels.add(i)

        if deleted_channels:
            # ? self.object_doc.data.{subcategory}.{option} = list(self.get_channel_ids() - self.selected)
            setattr(
                getattr(
                    self.object_doc.data, self.config_subcategory.name),
                self.option_value(),
                list(self.get_channel_ids() - deleted_channels))
            await self.object_doc.save_changes()

        self.generate_embed()

    def option_value(self) -> str:
        return getattr(getattr(self.object_doc.config, self.config_subcategory.name), self.option.name).name

    def get_channel_ids(self) -> set[int]:
        return {i for i in getattr(getattr(self.object_doc.data, self.config_subcategory.name), self.option_value())}

    def get_channels(self) -> list[GuildChannel]:
        return [self.user.guild.get_channel(i) for i in self.get_channel_ids()]

    def generate_embed(self) -> None:
        self.embed = Embed(
            title=f'configure {self.config_subcategory.name} {self.option_value()}',
            description=f'currently {self.option_value()}ed:\n' +
            '\n'.join([c.mention for c in self.get_channels()]),
            color=self.master.embed_color)

    @channel_select(
        placeholder='select some channels',
        min_values=0,
        max_values=25,
        custom_id='configure_channels_select',
        row=1)
    async def configure_channels_select(self, select: Select, interaction: Interaction) -> None:
        self.selected = {i.id for i in select.values}
        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='add',
        style=ButtonStyle.green,
        custom_id='configure_channels_add',
        row=2)
    async def configure_channels_add(self, button: Button, interaction: Interaction) -> None:
        # ? self.object_doc.data.{subcategory}.{option} = list(self.get_channel_ids() | self.selected)
        setattr(
            getattr(
                self.object_doc.data, self.config_subcategory.name),
            self.option_value(),
            list(self.get_channel_ids() | self.selected))

        await self.object_doc.save_changes()
        self.generate_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='remove',
        style=ButtonStyle.red,
        custom_id='configure_channels_remove',
        row=2)
    async def configure_channels_remove(self, button: Button, interaction: Interaction) -> None:
        # ? self.object_doc.data.{subcategory}.{option} = list(self.get_channel_ids() - self.selected)
        setattr(
            getattr(
                self.object_doc.data, self.config_subcategory.name),
            self.option_value(),
            list(self.get_channel_ids() - self.selected))

        await self.object_doc.save_changes()
        self.generate_embed()

        await interaction.response.edit_message(embed=self.embed, view=self)
