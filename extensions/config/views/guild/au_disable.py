from discord.ui import Button,button,Item,Select,string_select,InputText
from discord import Interaction,Embed,Guild,Member,SelectOption
from utils.classes import EmptyView,CustomModal
from client import Client


class au_disable_view(EmptyView):
	def __init__(self,original_view:EmptyView,user:Member,guild:Guild,client:Client,embed:Embed) -> None:
		super().__init__(timeout=0)
		self.original_view = original_view
		self.user          = user
		self.guild         = guild
		self.client        = client
		self.embed         = embed
		self.selected      = None
		self.disabled			 = []
		self.embed.title   = 'disable auto responses'
		self.add_items(self.back_button,self.au_select,self.manual_input_button,self.disable_button,self.enable_button)

	async def start(self,**kwargs) -> None: await self.reload()

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await self.client.on_error(interaction,error)
	
	@property
	def selected(self) -> str|None:
		return self._selected

	@selected.setter
	def selected(self,value:str|None) -> None:
		self._selected = value if value in self.client.au.keys() else None

	async def reload(self) -> None:
		self.disabled = await self.client.db.guild(self.guild.id).data.auto_responses.disabled.read()
		self.embed.description = f'currently disabled:\n'+('\n'.join([f'`{i}`' for i in self.disabled][:100]) or 'None')
		self.get_item('au_select').options = ([SelectOption(label=self.selected,description='manual input',default=True)] if (self.selected is not None and self.selected not in self.client.au.keys()) else [])+[SelectOption(label=i,default=i==self.selected) for i in await self.client.db.user(self.user.id).data.au.read()][:24]
		self.get_item('au_select').disabled = len(self.disabled) >= 100
		self.get_item('enable_button').disabled = self.selected is None or self.selected not in self.disabled
		self.get_item('disable_button').disabled = self.selected is None or self.selected in self.disabled

	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.edit_message(embed=self.original_view.embed,view=self.original_view)
		self.stop()

	@string_select(
		placeholder='select an auto response',
		custom_id='au_select',row=0,options=[SelectOption(label='loading...')])
	async def au_select(self,select:Select,interaction:Interaction) -> None:
		self.selected = select.values[0]
		await self.reload()
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='manual input',style=1,row=1,
		custom_id='manual_input_button')
	async def manual_input_button(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(self,'manual auto response input',
			[InputText(label='auto response trigger',value=self.selected or None)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		self.selected = modal.children[0].value
		await self.reload()
		await modal.interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='enable',style=3,row=1,
		custom_id='enable_button')
	async def enable_button(self,button:Button,interaction:Interaction) -> None:
		if self.selected in await self.client.db.guild(self.guild.id).data.auto_responses.disabled.read():
			await self.client.db.guild(self.guild.id).data.auto_responses.disabled.remove(self.selected)
		await self.reload()
		await interaction.response.edit_message(view=self,embed=self.embed)
	
	@button(
		label='disable',style=4,row=1,
		custom_id='disable_button')
	async def disable_button(self,button:Button,interaction:Interaction) -> None:
		if self.selected not in await self.client.db.guild(self.guild.id).data.auto_responses.disabled.read():
			await self.client.db.guild(self.guild.id).data.auto_responses.disabled.append(self.selected)
		await self.reload()
		await interaction.response.edit_message(view=self,embed=self.embed)