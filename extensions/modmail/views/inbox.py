from discord import Embed, Interaction, Guild, User, Member, SelectOption, ButtonStyle
from utils.pycord_classes import SubView, MasterView
from discord.ui import string_select, Select
from .thread import ModMailThreadView
from discord.ui import button, Button


class ModMailInboxView(SubView):
    def __init__(self, master: MasterView, user: User | Member, guild: Guild | None) -> None:
        super().__init__(master)
        self.user = user
        self.guild = guild
        self.page = 0
        self.embed = Embed(
            title='modmail inbox',
            description='check your modmail inbox',
            color=self.master.embed_color
        )

    async def __ainit__(self) -> None:
        self.add_items(self.back_button, self.select_thread)
        await self.reload_options()

    async def __on_back__(self) -> None:
        await self.reload_options()

    async def reload_options(self) -> None:
        user_doc = await self.client.db.user(self.user.id)

        threads = list(user_doc.data.modmail_threads.items())
        options = {}
        self.pages = (len(threads)//25) - (0 if len(threads) % 25 else 1)

        if len(threads) > 25:
            self.add_items(self.button_previous, self.button_next)
            self.page = 0 if self.page < 0 else self.pages if self.page > self.pages else self.page
            self.get_item('button_next').disabled = self.page == self.pages
            self.get_item('button_previous').disabled = self.page == 0

        for doc_id, last_read in threads[25*self.page:25*(self.page+1)]:
            thread_doc = await self.client.db.modmail(doc_id)
            unread_messages = len(thread_doc.messages)-last_read
            description_message = thread_doc.messages[-1].content

            options[
                SelectOption(
                    label=f'{f"({unread_messages}) " if unread_messages else ""}{thread_doc.title}',
                    description=(
                        description_message
                        if len(description_message) < 100 else
                        f'{description_message[:97]}...'
                    ),
                    value=doc_id)
            ] = thread_doc.messages[-1].timestamp

        self.get_item('select_thread').options = [
            option
            for option, _ in
            sorted(
                options.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ]

    @string_select(
        placeholder='select a modmail thread',
        row=1,
        custom_id='select_thread')
    async def select_thread(self, select: Select, interaction: Interaction) -> None:
        view = self.master.create_subview(
            ModMailThreadView,
            user=self.user,
            guild=self.guild,
            modmail_id=select.values[0]
        )

        await view.__ainit__()
        await interaction.response.edit_message(embeds=view.embeds, view=view)

    @button(
        label='⬅️',
        style=ButtonStyle.gray,
        row=2,
        custom_id='button_previous')
    async def button_previous(self, button: Button, interaction: Interaction) -> None:
        self.page -= 1
        await self.reload_options()
        await interaction.response.edit_message(embeds=self.embeds, view=self)

    @button(
        label='➡️',
        style=ButtonStyle.gray,
        row=2,
        disabled=True,
        custom_id='button_next')
    async def button_next(self, button: Button, interaction: Interaction) -> None:
        self.page += 1
        await self.reload_options()
        await interaction.response.edit_message(embeds=self.embeds, view=self)
