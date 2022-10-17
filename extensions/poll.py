from discord import SelectOption,Interaction,Embed,ApplicationContext,InputTextStyle
from discord.ui import View,Button,Select,button,Modal,InputText,Item
from discord.commands import slash_command
from discord.ext.commands import Cog
from main import client_cls


class published_dropdown(Select):
	def __init__(self,client:client_cls,options:list[SelectOption]) -> None:
		self.client = client
		if options is None: options = range(25)
		super().__init__(
			placeholder='vote for an option',
			min_values=0,
			max_values=1,
			options=options,
			custom_id='test2')

	async def callback(self,interaction:Interaction) -> None:
		data:dict = await self.client.db.polls.read(interaction.message.id)
		if str(interaction.user.id) in data['voters'].keys():
			await self.client.db.polls.dec(interaction.message.id,['options',data['voters'][str(interaction.user.id)],'votes'])
			data['options'][data['voters'][str(interaction.user.id)]]['votes'] -= 1
		await self.client.db.polls.inc(interaction.message.id,['options',self.values[0],'votes'])
		data['options'][self.values[0]]['votes'] += 1
		await self.client.db.polls.write(interaction.message.id,['voters',str(interaction.user.id)],self.values[0])
		options = data['options']
		embed = Embed(title=data['embed']['title'],description=data['embed']['description'],color=data['embed']['color'])
		for k,v in options.items(): embed.add_field(name=f'{v["votes"]} | {k}',value=v['description'],inline=False)
		await interaction.response.edit_message(embed=embed)
		await self.client.log.debug('responded to interaction callback')
		

class published_view(View):
	def __init__(self,*,client:client_cls,options:dict=None) -> None:
		self.client = client
		super().__init__(timeout=None)
		self.add_item(published_dropdown(client,[SelectOption(label=k) for k,v in options.items()] if options is not None else None))
	
	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await interaction.response.send_message(error,ephemeral=True)
		await self.client.log.error(error)

class input_text(Modal):
	def __init__(self,attrs:tuple[client_cls,View,Embed],title:str,items:list[InputText]) -> None:
		self.client,self.view,self.embed = attrs
		super().__init__(title=title)
		for i in items: self.add_item(i)
		# self.add_item(InputText(label='title',max_length=256,style=1))
		# self.add_item(InputText(label='description',max_length=1024,required=False,style=2,value='​'))

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

		await interaction.response.edit_message(embed=self.embed,view=self.view)

class view(View):
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
		modal = input_text((self.client,self,self.embed),'set title and description',[
			InputText(label='title',max_length=256,style=InputTextStyle.short),
			InputText(label='description',max_length=1024,required=False,style=InputTextStyle.long)])
		await interaction.response.send_modal(modal)
		self.title_set = True

	@button(label='add option',style=1,row=1)
	async def button_add_option(self,button:Button,interaction:Interaction) -> None:
		if len(self.options) >= 25:
			await interaction.response.send_message('max options reached')
			return
		modal = input_text((self.client,self,self.embed),'add option',[
			InputText(label='name',max_length=90,style=InputTextStyle.short),
			InputText(label='description',max_length=1024,required=False,style=InputTextStyle.long)])
		await interaction.response.send_modal(modal)

	@button(label='remove option',style=1,row=1)
	async def button_remove_option(self,button:Button,interaction:Interaction) -> None:
		modal = input_text((self.client,self,self.embed),'remove option',[
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
		msg = await interaction.channel.send(embed=embed,view=published_view(client=self.client,options=options))
		await self.client.db.polls.new(msg.id,{'_id':msg.id,'options':options,'embed':{'title':embed.title,'description':embed.description,'color':embed.color.value},'voters':{}})

class poll_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

	@Cog.listener()
	async def on_ready(self) -> None:
		self.client.add_view(published_view(client=self.client))

	@slash_command(name='poll',
		description='create a poll',
		guild_only=True)
	async def poll(self,ctx:ApplicationContext) -> None:
		embed = Embed(title='set a poll title!',description='and the description too!\nif you want, i guess. a description isn\'t required.',color=await self.client.embed_color(ctx))
		await ctx.response.send_message(embed=embed,
		view=view(
			client=self.client,
			embed=embed),
			ephemeral=True)

def setup(client:client_cls) -> None:
	client.add_cog(poll_cog(client))