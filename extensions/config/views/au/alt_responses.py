from discord.ui import Button,button,Select,string_select,InputText
from utils.classes import EmptyView,CustomModal,AutoResponse
from discord import Interaction,Embed,SelectOption

class alt_responses_view(EmptyView):
	def __init__(self,back_view:EmptyView) -> None:
		super().__init__(timeout=0)
		self.back_view = back_view
		self.au:AutoResponse = back_view.selected_au
		self.embed:Embed = back_view.embed.copy()
		self.embed.title = f'{self.au.trigger} alt responses'
		self.selected:str = None
		self.add_items(self.back_button,self.response_select,self.add_button)
		self.update()

	def update(self):
		self.embed.clear_fields()
		weights,responses = zip(*[(w,r) for w,r in [(None,self.au.response)]+self.au.alt_responses])
		auto_weight = (100-sum(filter(None,weights)))/weights.count(None)
		select_options = [SelectOption(label=r,default=r==self.selected) for r in responses[1:]]
		self.get_item('response_select').options = select_options or [SelectOption(label='None')]
		self.get_item('response_select').disabled = not bool(select_options)
		for weight,response in zip(weights,responses):
			self.embed.add_field(name=f'{weight or f"(auto) {round(auto_weight,2)}"}%',value=response,inline=False)

	async def modify_modal(self,interaction:Interaction,edit:tuple[float|int,str]=None) -> tuple[Interaction,tuple[float|None,str]]:
		weight,response = (None,None) if edit is None else edit
		modal = CustomModal(self,'add alt response' if edit is None else 'edit alt response',[
			InputText(label='% chance 0.01-99.99',placeholder='leave blank for auto',value=str(weight) if weight else weight,max_length=5,required=False),
			InputText(label='response message',value=response,max_length=100,required=True)])
		await interaction.response.send_modal(modal)
		all_weights = [w for w,r in self.au.alt_responses]
		weight_sum = sum(filter(None,all_weights))+(0.01*len(all_weights))
		await modal.wait()
		if modal.children[1].value in [self.au.response]+[r for w,r in self.au.alt_responses] and not edit:
			await modal.interaction.response.defer()
			raise ValueError('that message is already a response!')
		if modal.children[0].value:
			weight = float(modal.children[0].value)
			if not 0.01 <= weight <= 99.99:
				await modal.interaction.response.defer()
				raise ValueError('weight must be between 0.01 and 99.99 inclusive')
			if weight+weight_sum > 100:
				await modal.interaction.response.defer()
				raise ValueError(f'total weight cannot be above 100%\nmax available value is {round(100-weight_sum,2)}%')
		return (modal.interaction,(weight,modal.children[1].value))

	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		self.back_view.selected_au = self.au
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
		modal_interaction,alt_response = await self.modify_modal(interaction)
		self.au.alt_responses.append(alt_response)
		self.update()
		await modal_interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='edit',style=1,row=1,
		custom_id='edit_button')
	async def edit_button(self,button:Button,interaction:Interaction) -> None:
		old_alt_response = [(w,r) for w,r in self.au.alt_responses if r == self.selected][0]
		modal_interaction,alt_response = await self.modify_modal(interaction,old_alt_response)
		self.au.alt_responses.remove(old_alt_response)
		self.au.alt_responses.append(alt_response)
		self.update()
		await modal_interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=1,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		self.au.alt_responses.remove([(w,r) for w,r in self.au.alt_responses if r == self.selected][0])
		self.selected = None
		self.update()
		await interaction.response.edit_message(embed=self.embed,view=self)