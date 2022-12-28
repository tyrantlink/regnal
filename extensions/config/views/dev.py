from discord.ui import View,Button,button,Item,channel_select,Select
from extensions._shared_vars import config_info
from discord import Interaction,Embed
from client import Client,EmptyView

class dev_config(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.back_view    = back_view
		self.client       = client
		self.embed        = Embed(title='dev config',color=embed_color or back_view.embed.color)
		self.config       = {}
		self.selected     = None
		if back_view is not None: self.add_item(self.back_button)
		self.add_items(self.option_select)