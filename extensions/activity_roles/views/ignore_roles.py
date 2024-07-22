from discord import Member, Embed, Interaction, ButtonStyle
from discord.ui import button, role_select, Button, Select
from utils.pycord_classes import SubView, MasterView
from utils.db.documents import Guild as GuildDoc
from typing import Literal


class ActivityRolesIgnoreView(SubView):
    def __init__(self, master: MasterView, user: Member) -> None:
        super().__init__(master)
        self.user = user
        self.selected_roles: set[int] = set()

    async def __ainit__(self) -> None:
        assert await self.client.permissions.check(
            'activity_roles.ignore',
            self.user,
            self.user.guild
        )

        await self.reload_embed()

        self.add_items(
            self.user_select,
            self.back_button,
            self.button_ignore,
            self.button_unignore
        )

    async def reload_embed(self, guild_doc: GuildDoc | None = None) -> None:
        guild_doc = guild_doc or await self.client.db.guild(self.user.guild.id)

        self.embed = Embed(
            title='ignore roles',
            description='users with any one of these roles will not receive the activity role',
            color=self.master.embed_color
        )

        ignored_roles = '\n'.join(
            [f'<@&{i}>' for i in guild_doc.config.activity_roles.ignored_roles]
        )

        self.embed.add_field(
            name='ignored roles:',
            value=(
                ignored_roles
                if len(ignored_roles) < 1024
                else f'{ignored_roles[:1021]}...')
            or 'None'
        )

    async def log_action(self, action: Literal['ignore', 'unignore'], old_value: set[int]) -> None:
        guild_doc = await self.client.db.guild(self.user.guild.id)

        if (
            not guild_doc.config.logging.enabled or
            guild_doc.config.logging.channel is None or
            not guild_doc.config.logging.log_commands
        ):
            return

        channel = (
            self.user.guild.get_channel(guild_doc.config.logging.channel) or
            await self.client.fetch_channel(guild_doc.config.logging.channel)
        )

        if channel is None:
            return

        changed = self.selected_roles - (
            old_value
            if action == 'ignore' else
            self.selected_roles & old_value
        )

        embed = Embed(
            color=0xff6969 if action == 'ignore' else 0xffff69
        )

        embed.set_author(
            name=f'{self.user.display_name} {action}d roles from activity roles',
            icon_url=self.user.display_avatar.url
        )

        embed.add_field(
            name=f'{action}d roles',
            value='\n'.join([f'<@&{i}>' for i in changed])
        )

        await channel.send(embed=embed)

    @role_select(
        placeholder='select roles to ignore',
        row=0,
        max_values=25,
        custom_id='user_select')
    async def user_select(self, select: Select, interaction: Interaction) -> None:
        self.selected_roles = {i.id for i in select.values}
        await interaction.response.defer()

    @button(
        label='ignore',
        style=ButtonStyle.red,
        row=2,
        custom_id='button_ignore')
    async def button_ignore(self, button: Button, interaction: Interaction) -> None:
        guild_doc = await self.client.db.guild(self.user.guild.id)

        await self.log_action(
            'ignore',
            set(guild_doc.config.activity_roles.ignored_roles)
        )

        guild_doc.config.activity_roles.ignored_roles = list(
            set(guild_doc.config.activity_roles.ignored_roles) | self.selected_roles
        )

        await guild_doc.save_changes()
        await self.reload_embed(guild_doc)

        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='unignore',
        style=ButtonStyle.green,
        row=2,
        custom_id='button_unignore')
    async def button_unignore(self, button: Button, interaction: Interaction) -> None:
        guild_doc = await self.client.db.guild(self.user.guild.id)

        await self.log_action(
            'unignore',
            set(guild_doc.config.activity_roles.ignored_roles)
        )

        guild_doc.config.activity_roles.ignored_roles = list(
            set(guild_doc.config.activity_roles.ignored_roles) -
            self.selected_roles
        )

        await guild_doc.save_changes()
        await self.reload_embed(guild_doc)

        await interaction.response.edit_message(embed=self.embed, view=self)
