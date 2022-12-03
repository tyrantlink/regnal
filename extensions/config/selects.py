from discord import SelectOption,Interaction
from discord.ui import View,Select
from .shared import config


class config_select(Select):
	def __init__(self,view:View) -> None:
		self.v = view
		super().__init__(placeholder='select an option',options=[SelectOption(label=k) for k,v in config[self.v.current_menu].items()])
	
	async def callback(self,interaction:Interaction) -> None:
		for i in [self.v.button_enable,self.v.button_disable,self.v.button_input]:
			if i in self.v.children: self.v.remove_item(i)
		self.v.selected = self.values[0]
		self.v.embed.description = f'selected: {self.v.selected}'
		match config[self.v.current_menu][self.v.selected]['type']:
			case 'bool':
				self.v.add_item(self.v.button_enable)
				self.v.add_item(self.v.button_disable)
			case 'input':
				self.v.add_item(self.v.button_input)
			case 'str':
				self.v.add_item(self.v.button_enable)
				self.v.add_item(self.v.button_whitelist)
				self.v.add_item(self.v.button_blacklist)
				self.v.add_item(self.v.button_disable)
			case _: await self.v.client.log.debug('unknown config type in base_config_menu callback')
		await self.v.update_self(self.v)
		await interaction.response.edit_message(embed=self.v.embed,view=self.v)
