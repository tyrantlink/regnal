from discord import Interaction,Embed,User,Guild,SelectOption,InputTextStyle
from discord.ui import Button,button,Select,string_select,InputText
from client import Client,EmptyView,CustomModal

class publish_view(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,embed:Embed,version:str) -> None:
		super().__init__(timeout=0)
		self.back_view = back_view
		self.client    = client
		self.embed     = embed
		self.version   = version
		self.add_items(self.back_button,self.submit_button)

	@button(
		label='<',style=2,
		custom_id='back_button',row=0)
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.edit_message(view=self.back_view,embed=self.back_view.embed)
		self.stop()

	@button(
		label='submit',style=3,
		custom_id='submit_button',row=0)
	async def submit_button(self,button:Button,interaction:Interaction) -> None:
		channel = await self.client.db.inf('/reg/nal').config.change_log.read()
		channel = self.client.get_channel(channel) or await self.client.fetch_channel(channel)
		await (await channel.send(embed=self.embed)).publish()
		if 'hide' not in self.version: await self.client.db.inf('/reg/nal').version.write(self.version)
		await interaction.response.edit_message(view=None,embed=Embed(title='successfully announced commit',color=self.embed.color))
		self.stop()
	

class commit_view(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,user:User,version:str,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.back_view = back_view
		self.client    = client
		self._version  = [int(i) for i in version.split('.')]
		self.version   = version
		self.fields    = {}
		self.selected  = None
		self.title     = 'no title'
		self.embed     = Embed(title=f'v{version} | no title',color=embed_color)
		self.embed.set_author(name=user.name,icon_url=user.avatar.url)

	async def start(self,**kwargs) -> None:
		guild:Guild = kwargs.pop('guild')
		self.donator_fields = {f'{role.name} tier':'\n'.join(m.mention for m in role.members) for role in [guild.get_role(i) for i in await self.client.db.inf('/reg/nal').config.donation_roles.read()] if role.members}
		self.donator_fields = dict(list(self.donator_fields.items())+[('please report bugs with /issue','[development server](<https://discord.gg/4mteVXBDW7>)')])
		self.reload()
		
	def reload(self) -> None:
		self.embed.clear_fields()
		self.clear_items()
		self.embed.title = self.title if 'hide' in self.version else f'v{self.version} | {self.title}'
		self.embed.set_footer(text=f'version {self.version.replace("hide","")} ({self.client.commit_id})')
		fields = list(self.fields.items())+list(self.donator_fields.items())
		for n,v in fields: self.embed.add_field(name=n,value=v,inline=False)
		self.add_items(self.field_select,self.back_button,self.add_button,self.title_button,self.publish_button)
		self.get_item('field_select').options = [SelectOption(label=k,description=v.split('\n')[0][:100],value=str(i)) for i,(k,v) in enumerate(self.fields.items())] or [SelectOption(label='None')]
		self.get_item('field_select').disabled = self.get_item('field_select').options[0].value == 'None'
		self.get_item('add_button').disabled = len(fields) >= 25
		if self.selected is not None:
			self.get_item('field_select').options[self.selected].default = True
			self.add_items(self.edit_button,self.remove_button)
			self.get_item('remove_button').label = 'remove'
		self.add_item(self.vbump_button)

	@string_select(
		placeholder='select a field',
		custom_id='field_select',row=0,min_values=0)
	async def field_select(self,select:Select,interaction:Interaction) -> None:
		self.selected = int(select.values[0]) if select.values else None
		self.reload()
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='<',style=2,
		custom_id='back_button',row=1)
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.edit_message(view=self.back_view,embed=self.back_view.embed)
		self.stop()

	@button(
		label='add',style=3,
		custom_id='add_button',row=1)
	async def add_button(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(self,f'set commit title',
			[InputText(label='name',max_length=256),
			 InputText(label='value',max_length=1024,style=InputTextStyle.long)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		self.fields = dict(list(self.fields.items())+list({modal.children[0].value:modal.children[1].value}.items()))
		self.reload()
		await modal.interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='edit',style=1,
		custom_id='edit_button',row=1)
	async def edit_button(self,button:Button,interaction:Interaction) -> None:
		fields = list(self.fields.items())
		n,v = fields.pop(self.selected)
		modal = CustomModal(self,f'set commit title',
			[InputText(label='name',max_length=256,value=n),
			 InputText(label='value',max_length=1024,value=v,style=InputTextStyle.long)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		fields.insert(self.selected,(modal.children[0].value,modal.children[1].value))
		self.fields = dict(fields)
		self.reload()
		await modal.interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='remove',style=4,
		custom_id='remove_button',row=1)
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		fields = list(self.fields.items())
		fields.pop(self.selected)
		self.fields = dict(fields)
		self.selected = None
		self.reload()
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='vbump none',style=1,
		custom_id='vbump_button',row=1)
	async def vbump_button(self,button:Button,interaction:Interaction) -> None:
		ma,mi,p = self._version
		match button.label.split(' ')[-1]:
			case 'none':
				button.label = 'vbump patch'
				self.version = '.'.join([str(i) for i in [ma,mi,p+1]])
			case 'patch':
				button.label = 'vbump minor'
				self.version = '.'.join([str(i) for i in [ma,mi+1,0]])
			case 'minor':
				button.label = 'vbump major'
				self.version = '.'.join([str(i) for i in [ma+1,0,0]])
			case 'major':
				button.label = 'vbump hide'
				self.version = 'hide'+'.'.join([str(i) for i in [ma,mi,p]])
			case 'hide':
				button.label = 'vbump none'
				self.version = '.'.join([str(i) for i in [ma,mi,p]])
		self.reload()
		await interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='set title',style=1,
		custom_id='title_button',row=2)
	async def title_button(self,button:Button,interaction:Interaction) -> None:
		self.rm_confirmation = False
		modal = CustomModal(self,f'set commit title',
			[InputText(label='title',max_length=240,value=self.title)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		self.title = modal.children[0].value
		self.reload()
		await modal.interaction.response.edit_message(view=self,embed=self.embed)

	@button(
		label='publish',style=3,
		custom_id='publish_button',row=2)
	async def publish_button(self,button:Button,interaction:Interaction) -> None:
		view = publish_view(self,self.client,self.embed,self.version)
		await interaction.response.edit_message(view=view,embed=view.embed)