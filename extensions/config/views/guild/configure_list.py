from discord.ui import Button,button,Item,channel_select,Select
from discord import Interaction,Embed
from client import Client,EmptyView


class configure_list_view(EmptyView):
	def __init__(self,option_type:str,original_view:EmptyView,client:Client,embed:Embed) -> None:
		super().__init__(timeout=0)
		self.option_type    = option_type
		self.original_view  = original_view
		self.client         = client
		self.embed          = embed
		self.add_items(self.channel_select,self.back_button,self.add_button,self.remove_button)

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await self.client.on_error(interaction,error)

	async def reload(self,guild_id) -> None:
		self.embed.description = f'currently {self.option_type[1]}ed:\n'+('\n'.join([f'<#{i}>' for i in await self.client.db.guilds.read(guild_id,['data',self.option_type[0],self.option_type[1]])]) or 'None')

	@channel_select(
		custom_id='channel_select',row=0,
		placeholder='select some channels',max_values=25)
	async def channel_select(self,select:Select,interaction:Interaction) -> None:
		self.channels_selected = select.values
		await interaction.response.edit_message(embed=self.embed,view=self)
	
	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.edit_message(embed=self.original_view.embed,view=self.original_view)

	@button(
		label='add',style=3,row=1,
		custom_id='add_button')
	async def add_button(self,button:Button,interaction:Interaction) -> None:
		current:list = await self.client.db.guilds.read(interaction.guild.id,['data',self.option_type[0],self.option_type[1]])
		for i in self.channels_selected:
			if i.id not in current: current.append(i.id)
		await self.client.db.guilds.write(interaction.guild.id,['data',self.option_type[0],self.option_type[1]],current)
		await self.reload(interaction.guild.id)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=1,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		current:list = await self.client.db.guilds.read(interaction.guild.id,['data',self.option_type[0],self.option_type[1]])
		for i in self.channels_selected:
			if i.id in current: current.remove(i.id)
		await self.client.db.guilds.write(interaction.guild.id,['data',self.option_type[0],self.option_type[1]],current)
		await self.reload(interaction.guild.id)
		await interaction.response.edit_message(embed=self.embed,view=self)