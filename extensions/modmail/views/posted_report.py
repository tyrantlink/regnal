from discord import Interaction, ButtonStyle, Embed
from asyncio import sleep, create_task
from utils.pycord_classes import View
from discord.ui import button, Button
from client import Client


# ? leaving the reopen code commented out while i decide if i want to keep it

class ModMailPostedReportView(View):
    def __init__(self, client: Client, add_all: bool = False) -> None:
        super().__init__(timeout=None)
        self.client = client
        self.add_items(self.button_close, self.button_toggle_sendall)
        # if add_all:
        # 	self.add_items(self.button_reopen)

    async def close_confirm_timer(self, interaction: Interaction) -> None:
        await sleep(45)

        if self.get_item('button_close').label == 'closed':
            return

        self.get_item('button_close').label = 'close'
        await interaction.edit_original_response(view=self)

    @button(
        label='close',
        style=ButtonStyle.red,
        custom_id='button_close')
    async def button_close(self, button: Button, interaction: Interaction) -> None:
        if not (
            await self.client.permissions.check(
                'modmail.close_thread',
                interaction.user,
                interaction.guild
            )
        ):
            await interaction.response.send_message(
                'you do not have permission to close this thread',
                ephemeral=True)
            return

        if button.label == 'close':
            button.label = 'confirm close'
            await interaction.response.edit_message(view=self)
            await interaction.followup.send('please press the button again to confirm\nonce the thread is closed no more messages can be sent', ephemeral=True)
            create_task(self.close_confirm_timer(interaction.message))
            return

        modmail_id = interaction.message.embeds[-1].footer.text.split(': ')[-1]
        modmail = await self.client.db.modmail(f'{interaction.guild.id}:{modmail_id}')
        modmail.closed = True

        await modmail.save_changes()

        await interaction.channel.send(f'''
            this thread was closed by {interaction.user.mention}\n
            no more messages will be exchanged.\n
            archiving this thread is recommended.
            '''.replace('    ', '').strip()
        )

        button.label = 'closed'
        button.disabled = True

        await interaction.response.edit_message(view=self)

    @ button(
        label='only sending mentions',
        style=ButtonStyle.gray,
        custom_id='button_toggle_sendall')
    async def button_toggle_sendall(self, button: Button, interaction: Interaction) -> None:
        modmail_id = interaction.message.embeds[-1].footer.text.split(': ')[-1]

        modmail = await self.client.db.modmail(f'{interaction.guild.id}:{modmail_id}')

        match button.label:
            case 'only sending mentions':
                button.label = 'sending all messages'
                button.style = ButtonStyle.blurple
                modmail.send_all = True
            case 'sending all messages':
                button.label = 'only sending mentions'
                button.style = ButtonStyle.gray
                modmail.send_all = False

        await modmail.save_changes()
        await interaction.response.edit_message(view=self)

        log_embed = Embed(
            title='message sending changed!',
            description=(
                'all messages will be sent to the user'
                if modmail.send_all else
                f'only messages that ping {self.client.user.mention} (including replies) will be sent to the user'
            ),
            color=await self.client.helpers.embed_color(interaction.guild.id)
        )

        log_embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.avatar.url
        )

        await interaction.channel.send(embed=log_embed)

    # @button(
    # 	label = 'reopen',
    # 	style = ButtonStyle.blurple,
    # 	custom_id = 'button_reopen')
    # async def button_reopen(self,button:Button,interaction:Interaction) -> None:
    # 	self.get_item('button_close').label = 'close'
    # 	self.get_item('button_close').disabled = False
    # 	self.get_item('button_close').style = ButtonStyle.red
    # 	self.remove_item(self.button_reopen)
    # 	await interaction.response.edit_message(view=self)
