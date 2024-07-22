from discord import Member, Embed, Interaction, ButtonStyle
from discord.ui import button, user_select, Button, Select
from utils.pycord_classes import SubView, MasterView
from utils.db.documents import Guild as GuildDoc
from typing import Literal


class TTSBanningView(SubView):
    def __init__(self, master: MasterView, user: Member) -> None:
        super().__init__(master)
        self.user = user
        self.selected_users: set[int] = set()

    async def __ainit__(self) -> None:
        assert await self.client.permissions.check('tts.ban', self.user, self.user.guild)
        await self.reload_embed()

        self.add_items(
            self.user_select,
            self.back_button,
            self.button_ban,
            self.button_unban
        )

    async def reload_embed(self, guild_doc: GuildDoc | None = None) -> None:
        guild_doc = guild_doc or await self.client.db.guild(self.user.guild.id)

        self.embed = Embed(
            title='tts banning',
            description='prevent specific users from using tts',
            color=self.master.embed_color
        )

        banned_users = '\n'.join(
            [f'<@{i}>' for i in guild_doc.data.tts.banned]
        )

        self.embed.add_field(
            name='banned users:',
            value=(
                banned_users
                if len(banned_users) < 1024
                else f'{banned_users[:1021]}...'
            ) or 'None'
        )

    async def log_action(self, action: Literal['ban', 'unban'], old_value: set[int]) -> None:
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

        changed = self.selected_users - \
            old_value if action == 'ban' else self.selected_users & old_value

        embed = Embed(
            color=0xff6969 if action == 'ban' else 0xffff69
        )

        embed.set_author(
            name=f'{self.user.display_name} {action}ned users from tts',
            icon_url=self.user.display_avatar.url
        )

        embed.add_field(
            name=f'{action}ned users',
            value='\n'.join([f'<@{i}>' for i in changed])
        )

        await channel.send(embed=embed)

    @user_select(
        placeholder='select a users to ban',
        row=0,
        max_values=25,
        custom_id='user_select')
    async def user_select(self, select: Select, interaction: Interaction) -> None:
        self.selected_users = {i.id for i in select.values}
        await interaction.response.defer()

    @button(
        label='ban',
        style=ButtonStyle.red,
        row=2,
        custom_id='button_ban')
    async def button_ban(self, button: Button, interaction: Interaction) -> None:
        guild_doc = await self.client.db.guild(self.user.guild.id)

        await self.log_action('ban', set(guild_doc.data.tts.banned))

        guild_doc.data.tts.banned = list(
            set(guild_doc.data.tts.banned) | self.selected_users
        )

        await guild_doc.save_changes()
        await self.reload_embed(guild_doc)

        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(
        label='unban',
        style=ButtonStyle.green,
        row=2,
        custom_id='button_unban')
    async def button_unban(self, button: Button, interaction: Interaction) -> None:
        guild_doc = await self.client.db.guild(self.user.guild.id)

        await self.log_action('unban', set(guild_doc.data.tts.banned))

        guild_doc.data.tts.banned = list(
            set(guild_doc.data.tts.banned) - self.selected_users
        )

        await guild_doc.save_changes()
        await self.reload_embed(guild_doc)

        await interaction.response.edit_message(embed=self.embed, view=self)
