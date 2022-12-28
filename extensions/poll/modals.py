from discord.ui import View,Modal,InputText
from discord import Interaction,Embed
from client import Client


class poll_modal(Modal):
	def __init__(self,attrs:tuple[Client,View,Embed],title:str,items:list[InputText]) -> None:
		self.client,self.view,self.embed = attrs
		super().__init__(title=title)
		for i in items: self.add_item(i)

	async def callback(self,interaction:Interaction) -> None:
		match self.title:
			case 'set title and description': 
				self.embed.title = self.children[0].value
				self.embed.description = self.children[1].value
			case 'add option':
				for i in self.embed.fields:
					if i.name == self.children[0].value:
						await interaction.response.send_message(f'option {i.name} already exists',ephemeral=True)
						return
				self.view.options.append((self.children[0].value,self.children[1].value if self.children[1].value else '​'))
				self.embed.add_field(name=self.children[0].value,value=self.children[1].value if self.children[1].value else '​',inline=False)
			case 'remove option':
				for index,i in enumerate(self.embed.fields):
					if i.name == self.children[0].value:
						self.embed.remove_field(index)
						break
				else:
					await interaction.response.send_message(f'option {self.children[0].value} does not exist',ephemeral=True)
					return
				for i in self.view.options:
					if i[0] == self.children[0].value:
						self.view.options.remove(i)
						break

		await interaction.response.edit_message(embed=self.embed)
