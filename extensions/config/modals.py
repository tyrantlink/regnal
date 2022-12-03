from discord.ui import View,Modal,InputText
from discord import Interaction,Embed

class config_modal(Modal):
	def __init__(self,embed:Embed,view:View,label:str,placeholder:str,max_length:int) -> None:
		self.label = label
		self.embed = embed
		self.view = view
		super().__init__(title='set value')
		self.add_item(InputText(label=label,placeholder=placeholder,max_length=max_length))

	async def callback(self,interaction:Interaction) -> None:
		self.response = self.children[0].value
		for index,field in enumerate(self.embed.fields):
			if field.name.split(':')[0] == self.label:
				if self.label == 'embed_color':
					self.embed.set_field_at(index,name=f'{self.label}: #{self.response.upper()}',value=field.value)
					try: self.embed.color = int(self.response,16)
					except ValueError: pass
				else: self.embed.set_field_at(index,name=f'{self.label}: {self.response}',value=field.value)
		await interaction.response.edit_message(embed=self.embed,view=self.view)
		self.stop()
