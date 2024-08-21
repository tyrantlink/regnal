from discord import Interaction, SelectOption, User, Member, Embed
from utils.pycord_classes import SubView, MasterView
from discord.ui import string_select, Select
from .category import ConfigCategoryView


class ConfigHomeView(SubView):
    def __init__(self, master: 'MasterView', user: User | Member, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.add_item(self.category_select)
        self.user = user

    async def __ainit__(self) -> None:
        options = [
            SelectOption(label='user', description='user config')]

        if getattr(self.user, 'guild', None) is not None:
            if (bool(await self.client.permissions.user(self.user, self.user.guild)-{'dev'}) or
                    self.user.guild_permissions.manage_guild):
                options.append(SelectOption(
                    label='guild', description='guild config'))

        self.get_item('category_select').options = options

        self.embed = Embed(
            title='config', color=self.master.embed_color)
        self.embed.set_footer(text=f'config')

    async def get_view(self, value: str) -> ConfigCategoryView:
        match value:
            case 'user':
                view = self.master.create_subview(
                    ConfigCategoryView, self.client.config.data.user, user=self.user)
            case 'guild':
                view = self.master.create_subview(
                    ConfigCategoryView, self.client.config.data.guild, user=self.user)
            case _: raise ValueError('improper option selected, discord shouldn\'t allow this')

        await view.__ainit__()
        return view

    @string_select(
        placeholder='select a config category',
        custom_id='category_select')
    async def category_select(self, select: Select, interaction: Interaction) -> None:
        view = await self.get_view(select.values[0])
        await interaction.response.edit_message(view=view, embed=view.embed)
