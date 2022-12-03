from discord.ui import Modal,InputText,View
from discord import Interaction
from main import client_cls

class config_modal(Modal):
	def __init__(self,view:View,title:str,children:list[InputText]) -> None:
		self.view              = view
		self.client:client_cls = view.client
		self.interaction = None
		super().__init__(*children, title=title)

	async def callback(self, interaction: Interaction):
		self.interaction = interaction
		self.stop()