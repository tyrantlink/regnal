if not 'TYPE_HINT': from client import Client
from discord import ButtonStyle,Interaction
from utils.pycord_classes import View
from discord.ui import Button,button
from time import time


class EditedLogView(View):
	def __init__(self,client:'Client') -> None:
		super().__init__()
		self.client = client
		self.add_item(self.button_clear)
	
	@button(
		label='clear',custom_id='button_clear',
		style=ButtonStyle.red)
	async def button_clear(self,button:Button,interaction:Interaction) -> None:
		if not await self.client.permissions.check('logging.clear_logs',interaction.user,interaction.guild):
			await interaction.response.send_message('You do not have permission to clear logs!',ephemeral=True)
			return

		embed = interaction.message.embeds[0]
		embed.clear_fields()
		embed.add_field(
			name=f'CLEARED <t:{int(time())}:t>',
			value=f'logs cleared by {interaction.user.mention}')
		interaction.message.embeds = [embed]
		button.disabled = True
		await interaction.response.edit_message(embed=embed,view=self)

class DeletedLogView(View):
	def __init__(self,client:'Client',has_attachments:bool=True) -> None:
		super().__init__()
		self.client = client
		self.add_item(self.button_clear)
		if has_attachments: self.add_item(self.button_hide_attachments)

	@button(
		label='clear',custom_id='button_clear',
		style=ButtonStyle.red)
	async def button_clear(self,button:Button,interaction:Interaction) -> None:
		if not await self.client.permissions.check('logging.clear_logs',interaction.user,interaction.guild):
			await interaction.response.send_message('You do not have permission to clear logs!',ephemeral=True)
			return

		embed = interaction.message.embeds[0]
		embed.clear_fields()
		embed.add_field(
			name=f'CLEARED <t:{int(time())}:t>',
			value=f'logs cleared by {interaction.user.mention}')
		interaction.message.embeds = [embed]
		button.disabled = True
		await interaction.response.edit_message(embed=embed,view=self)

	@button(
		label='hide attachments',custom_id='button_hide_attachments',
		style=ButtonStyle.red)
	async def button_hide_attachments(self,button:Button,interaction:Interaction) -> None:
		if not await self.client.permissions.check('logging.hide_attachments',interaction.user,interaction.guild):
			await interaction.response.send_message('You do not have permission to hide attachments!',ephemeral=True)
			return
		
		embed = interaction.message.embeds[0]
		embed.fields[-1].value = f'attachments hidden by {interaction.user.mention}'
		interaction.message.embeds[0] = embed
		button.disabled = True
		await interaction.response.edit_message(embed=embed,view=self)

class BulkDeletedLogView(EditedLogView): ...