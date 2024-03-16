from utils.pycord_classes import SubView
from discord import Interaction
from discord.ui import Button
from client.config.models import AdditionalView


class AdditionalViewButton(Button):
	def __init__(self,parent:SubView,view:AdditionalView,*args,**kwargs) -> None:
		super().__init__(*args,**kwargs)
		self.parent = parent
		self.view_data = view
		self.label = view.button_label
		self.style = 1
		self.row = view.button_row
		self.custom_id = view.button_id

	async def callback(self,interaction:Interaction):
		view = self.parent.master.create_subview(
			view_cls = self.view_data.view,
			user = self.parent.user)
		await view.__ainit__()
		await interaction.response.edit_message(view=view,embed=view.embed)