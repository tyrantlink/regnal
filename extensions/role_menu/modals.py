from discord.ui import View,Modal,InputText
from discord import Interaction,Embed


class role_menu_modal(Modal):
	def __init__(self,embed:Embed,view:View,inputs=[InputText]) -> None:
		self.embed = embed
		self.view = view
		super().__init__(title='set placeholder')
		for i in inputs: self.add_item(i)

	async def callback(self,interaction:Interaction) -> None:
		self.response = [i.value for i in self.children]
		
		await interaction.response.edit_message(embed=self.embed,view=self.view)
		self.stop()
