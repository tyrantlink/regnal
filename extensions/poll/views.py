from discord import SelectOption,Interaction,Embed,InputTextStyle
from discord.ui import View,Button,button,InputText,Item
from .selects import poll_published_select
from .modals import poll_modal
from main import client_cls


class poll_published_view(View):
	def __init__(self,*,client:client_cls,options:dict=None) -> None:
		self.client = client
		super().__init__(timeout=None)
		self.add_item(poll_published_select(client,[SelectOption(label=k) for k,v in options.items()] if options is not None else None))

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)

class poll_view(View):
	def __init__(self,*,client:client_cls,embed:Embed) -> None:
		super().__init__()
		self.clear_items()
		self.client = client
		self.embed = embed
		self.title_set = False
		self.options = []
		self.add_item(self.button_set_title)
		self.add_item(self.button_add_option)
		self.add_item(self.button_remove_option)
		self.add_item(self.button_publish)

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)

	@button(label='set title and description',style=1,row=0)
	async def button_set_title(self,button:Button,interaction:Interaction) -> None:
		modal = poll_modal((self.client,self,self.embed),'set title and description',[
			InputText(label='title',max_length=256,style=InputTextStyle.short),
			InputText(label='description',max_length=1024,required=False,style=InputTextStyle.long)])
		await interaction.response.send_modal(modal)
		self.title_set = True

	@button(label='add option',style=1,row=1)
	async def button_add_option(self,button:Button,interaction:Interaction) -> None:
		if len(self.options) >= 25:
			await interaction.response.send_message('max options reached')
			return
		modal = poll_modal((self.client,self,self.embed),'add option',[
			InputText(label='name',max_length=90,style=InputTextStyle.short),
			InputText(label='description',max_length=1024,required=False,style=InputTextStyle.long)])
		await interaction.response.send_modal(modal)

	@button(label='remove option',style=1,row=1)
	async def button_remove_option(self,button:Button,interaction:Interaction) -> None:
		modal = poll_modal((self.client,self,self.embed),'remove option',[
			InputText(label='option',max_length=90,style=InputTextStyle.short)])
		await interaction.response.send_modal(modal)

	@button(label='publish',style=3,row=3)
	async def button_publish(self,button:Button,interaction:Interaction) -> None:
		if not self.title_set or len(self.options) < 2:
			await interaction.response.send_message('title and at least two options are required',ephemeral=True)
			return
		embed = Embed(title=self.embed.title,description=self.embed.description,color=self.embed.color.value)
		for i in self.options: embed.add_field(name=f'0 | {i[0]}',value=i[1],inline=False)
		options = {i[0]:{'description':i[1],'votes':0} for i in self.options}
		msg = await interaction.channel.send(embed=embed,view=poll_published_view(client=self.client,options=options))
		await self.client.db.polls.new(msg.id,{'_id':msg.id,'options':options,'embed':{'title':embed.title,'description':embed.description,'color':embed.color.value},'voters':{}})

