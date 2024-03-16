from utils.db.documents.guild import GuildDataQOTDQuestion
from discord import ButtonStyle,Interaction
from utils.pycord_classes import View
from discord.ui import Button,button
from client import Client
from time import time


class QOTDAskLog(View):
	def __init__(self,client:Client) -> None:
		super().__init__()
		self.client = client
		self.add_item(self.button_remove)

	@button(
		label='remove',custom_id='button_remove',
		style=ButtonStyle.red)
	async def button_remove(self,button:Button,interaction:Interaction) -> None:
		if not await self.client.permissions.check('qotd.remove_custom',interaction.user,interaction.guild):
			await interaction.response.send_message('You do not have permission to remove custom questions!',ephemeral=True)
			return
		embed = interaction.message.embeds[0]

		guild_doc = await self.client.db.guild(interaction.guild.id)
		question = GuildDataQOTDQuestion(
			question=embed.description,
			author=embed.author.name.removesuffix(' asked a custom question!'),
			icon=embed.author.icon_url)
		guild_doc.data.qotd.nextup.remove(question)
		await guild_doc.save_changes()

		embed.color = 0xff6969
		embed.add_field(
			name=f'REMOVED <t:{int(time())}:t>',
			value=f'custom question removed by {interaction.user.mention}')
		interaction.message.embeds = [embed]
		button.disabled = True
		await interaction.response.edit_message(embed=embed,view=self)