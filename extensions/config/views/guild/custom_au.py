from discord.ui import Button,button,Item,Select,string_select,user_select,InputText
from discord import Interaction,Embed,SelectOption,InputTextStyle
from client import Client,EmptyView,CustomModal


class custom_au_view(EmptyView):
	def __init__(self,original_view:EmptyView,client:Client,embed:Embed,custom_au:dict) -> None:
		super().__init__(timeout=0)
		self.original_view = original_view
		self.client        = client
		self.embed         = embed
		self.custom_au     = custom_au
		self.page          = 'main'
		self.selected_au   = None
		self.remove_confirmed = False
		self.new_au = None
		self.add_items(self.page_select,self.back_button)
	
	@property
	def default_new_au(self):
		return {
			'method':None,
			'trigger':None,
			'response':None,
			'user':None,
			'regex':False,
			'nsfw':False}

	def add_items(self,*items:Item) -> None:
		for item in items: self.add_item(item)
	
	def au_reload(self,guild_id:int) -> None:
		if (reload:=self.client.flags.get('RELOAD_AU',None)) is not None and guild_id not in reload:
			self.client.flags['RELOAD_AU'].append(guild_id)
		else:
			self.client.flags.update({'RELOAD_AU',[guild_id]})

	def reload(self) -> None:
		self.selected_au = None
		self.remove_confirmed = False
		self.embed.description = None
		self.embed.clear_fields()
		self.clear_items()
		match self.page:
			case 'main':
				self.add_items(self.page_select,self.back_button)
			case 'contains'|'exact'|'exact-cs':
				self.embed.add_field(name='method',value=self.page)
				self.add_items(self.custom_au_select,self.back_button,self.new_button)
				for child in self.children:
					if child.custom_id != 'new_button': continue
					if len(self.custom_au.get(self.page,{}).keys()) >= 25: child.disabled = True
					else: child.disabled = False
				self.update_select()
			case 'new':
				self.add_items(self.limit_user_select,self.back_button,self.set_button,self.regex_button,self.nsfw_button,self.save_button)
			case _: raise

	def update_select(self):
		for child in self.children:
			if child.custom_id != 'custom_au_select': continue
			if (options:=[SelectOption(label=k,description=v.get('response','').split('\n')[0][:100]) for k,v in self.custom_au.get(self.page,{}).items()]):
				child.options = options
				child.placeholder = 'select an auto response'
				child.disabled = False
			else:
				child.options = [SelectOption(label='None')]
				child.placeholder = 'there are no custom auto responses'
				child.disabled = True
			break

	def embed_au(self,au:dict):
		self.embed.clear_fields()
		self.embed.add_field(name='method',value=au.get('method','ERROR'))
		self.embed.add_field(name='match with regex',value=au.get('regex',False))
		self.embed.add_field(name='limited to user',value=f"<@{au.get('user',False)}>" if au.get('user',False) else False)
		self.embed.add_field(name='nsfw',value=au.get('nsfw',False))
		self.embed.add_field(name='trigger',value=au.get('trigger','ERROR'),inline=False)
		self.embed.add_field(name='response',value=au.get('response',False),inline=False)
		for child in self.children:
			match child.custom_id:
				case 'regex_button': child.style = 3 if au.get('regex',False) else 4
				case 'nsfw_button': child.style = 3 if au.get('nsfw',False) else 4
				case _: continue

	@string_select(
		custom_id='page_select',row=0,
		placeholder='select a category',
		options=[SelectOption(label=i) for i in ['contains','exact','exact-cs']])
	async def page_select(self,select:Select,interaction:Interaction) -> None:
		self.page = select.values[0]
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@string_select(
		custom_id='custom_au_select',row=0,
		placeholder='select an auto response')
	async def custom_au_select(self,select:Select,interaction:Interaction) -> None:
		self.selected_au = select.values[0]
		self.remove_confirmed = False
		self.embed.description = None
		au = self.custom_au.get(self.page,{}).get(self.selected_au,{})
		au.update({'method':self.page,'trigger':self.selected_au})
		self.embed_au(au)
		self.add_item(self.edit_button)
		if len(self.custom_au.get(self.page,{}).keys()) != 0: self.add_item(self.remove_button)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		if self.page == 'main':
			await interaction.response.edit_message(embed=self.original_view.embed,view=self.original_view)
			self.stop()
			return
		self.page = 'main'
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='new',style=3,row=1,
		custom_id='new_button')
	async def new_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au = self.default_new_au
		self.new_au.update({'method':self.page})
		self.page = 'new'
		self.reload()
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='edit',style=1,row=1,
		custom_id='edit_button')
	async def edit_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au = self.custom_au.get(self.page,{}).get(self.selected_au)
		self.new_au.update({'method':self.page})
		self.page = 'new'
		self.reload()
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=1,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		if self.remove_confirmed:
			if self.selected_au is None: raise
			self.custom_au[self.page].pop(self.selected_au)
			await self.client.db.guilds.unset(interaction.guild.id,['data','auto_responses','custom',self.page,self.selected_au.replace('.','\.')])
			self.au_reload(interaction.guild.id)
			self.reload()
		else:
			self.embed.description = 'are you sure you want to remove this auto response?\nclick remove again to remove it.'
			self.remove_confirmed = True
		await interaction.response.edit_message(embed=self.embed,view=self)

	@user_select(
		placeholder='limit to a user',
		custom_id='limit_user_select',min_values=0)
	async def limit_user_select(self,select:Select,interaction:Interaction) -> None:
		if select.values: self.new_au.update({'user':select.values[0].id})
		else: self.new_au.update({'user':None})
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='set',style=1,row=1,
		custom_id='set_button')
	async def set_button(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(self,'add custom auto response',[
			InputText(label='trigger message',placeholder='cannot start with $ or contain a .',min_length=1,max_length=100,style=InputTextStyle.short,value=self.new_au.get('trigger')),
			InputText(label='response',placeholder='"{none}" to give no response (used for disabling a default auto response)',min_length=1,max_length=500,style=InputTextStyle.long,value=self.new_au.get('response'))])
		
		await interaction.response.send_modal(modal)
		await modal.wait()
		if modal.children[0].value.startswith('$') or '.' in modal.children[0].value:
			embed = Embed(title='an error has occurred!',color=0xff6969)
			embed.add_field(name='error',value='auto response trigger cannot start with $ or contain a .')
			await modal.interaction.response.send_message(embed=embed,ephemeral=self.client.hide(interaction))
			return
		self.new_au.update({
			'trigger':modal.children[0].value,	
			'response':modal.children[1].value})
		self.embed_au(self.new_au)
		for child in self.children:
			if child.custom_id != 'save_button': continue
			child.disabled = False
			break
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='regex',style=4,row=1,
		custom_id='regex_button')
	async def regex_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au.update({'regex':not self.new_au.get('regex')})
		if self.new_au.get('regex'): button.style = 3
		else: button.style = 4
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='nsfw',style=4,row=1,
		custom_id='nsfw_button')
	async def nsfw_button(self,button:Button,interaction:Interaction) -> None:
		self.new_au.update({'nsfw':not self.new_au.get('nsfw')})
		if self.new_au['nsfw']: button.style = 3
		else: button.style = 4
		self.embed_au(self.new_au)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='save',style=3,row=2,
		custom_id='save_button',disabled=True)
	async def save_button(self,button:Button,interaction:Interaction) -> None:
		old_page = self.new_au.pop('method')
		self.custom_au[old_page][self.new_au.pop('trigger')] = self.new_au
		await self.client.db.guilds.write(interaction.guild.id,['data','auto_responses','custom',old_page],self.custom_au.get(old_page))
		self.au_reload(interaction.guild.id)
		self.page = old_page
		self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)