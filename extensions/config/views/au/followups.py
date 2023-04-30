from discord.ui import Button,button,Select,string_select,InputText
from utils.classes import EmptyView,CustomModal,AutoResponse
from discord import Interaction,Embed,SelectOption

class followups_view(EmptyView):
	def __init__(self,back_view:EmptyView) -> None:
		super().__init__(timeout=0)
		self.back_view = back_view
		self.au:AutoResponse = back_view.selected_au
		self.embed:Embed = back_view.embed.copy()
		self.embed.title = f'{self.au.trigger} followups'
		self.selected:str = None
		self.add_items(self.back_button,self.response_select,self.add_button)
		self.update()

	def update(self):
		self.embed.clear_fields()
		delays,followups = zip(*[(d,f) for d,f in [(0,self.au.response)]+self.au.followups])
		select_options = [SelectOption(label=f,default=f==self.selected) for f in followups[1:]]
		self.get_item('response_select').options = select_options or [SelectOption(label='None')]
		self.get_item('response_select').disabled = not bool(select_options)
		self.get_item('add_button').disabled = len(followups) >= 25
		for delay,followup in zip(delays,followups):
			self.embed.add_field(name=f'{delay} seconds',value=followup,inline=False)

	async def modify_modal(self,interaction:Interaction,edit:tuple[float|int,str]=None) -> tuple[Interaction,tuple[float|None,str]]:
		delay,followup = (None,None) if edit is None else edit
		modal = CustomModal(self,'add followup response' if edit is None else 'edit followup response',[
			InputText(label='delay (seconds)',value=str(delay) if delay else delay,max_length=5,required=True),
			InputText(label='response message',value=followup,max_length=100,required=True)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		try: delay = float(modal.children[0].value)
		except ValueError:
			await modal.interaction.response.defer()
			raise ValueError('delay must be a number')
		if not 0.01 <= delay <= 30.00:
			await modal.interaction.response.defer()
			raise ValueError('weight must be between 0.01 and 30.00 (inclusive)')
		return (modal.interaction,(delay,modal.children[1].value))

	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		self.back_view.selected_au = self.au
		self.back_view.page = 'new'
		self.back_view.embed_au()
		await interaction.response.edit_message(embed=self.back_view.embed,view=self.back_view)
		self.stop()

	@string_select(
		placeholder='select a response',row=0,
		custom_id='response_select',options=[SelectOption(label='None')])
	async def response_select(self,select:Select,interaction:Interaction) -> None:
		self.selected = select.values[0]
		self.add_items(self.edit_button,self.remove_button)
		self.update()
		await interaction.response.edit_message(view=self)

	@button(
		label='add',style=3,row=1,
		custom_id='add_button')
	async def add_button(self,button:Button,interaction:Interaction) -> None:
		modal_interaction,followup = await self.modify_modal(interaction)
		self.au.followups.append(followup)
		self.update()
		await modal_interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='edit',style=1,row=1,
		custom_id='edit_button')
	async def edit_button(self,button:Button,interaction:Interaction) -> None:
		old_followup_index = self.au.followups.index([(d,f) for d,f in self.au.followups if f == self.selected][0])
		modal_interaction,alt_response = await self.modify_modal(interaction,self.au.followups[old_followup_index])
		self.au.followups[old_followup_index] = alt_response
		self.update()
		await modal_interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=1,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		self.au.followups.remove([(d,f) for d,f in self.au.followups if f == self.selected][0])
		self.selected = None
		self.update()
		await interaction.response.edit_message(embed=self.embed,view=self)