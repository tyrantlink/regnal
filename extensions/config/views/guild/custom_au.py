from discord.ui import Button,button,Select,string_select,user_select,InputText
from discord import Interaction,Embed,SelectOption,InputTextStyle,Guild,Member
from utils.classes import EmptyView,CustomModal,AutoResponse
from client import Client


class custom_au_view(EmptyView):
	def __init__(self,original_view:EmptyView,user:Member,guild:Guild,client:Client,embed:Embed,custom_au:dict) -> None:
		super().__init__(timeout=0)
		self.original_view = original_view
		self.guild         = guild
		self.user          = user
		self.client        = client
		self.embed         = embed
		self.custom_au     = custom_au
		self.page          = 'main'
		self.selected_au:AutoResponse = None

	def set_au_reload_flag(self) -> None:
		if self.client.flags.get('RELOAD_AU',None) is None: self.client.flags.update({'RELOAD_AU':[]})
		if self.guild.id not in self.client.flags.get('RELOAD_AU'):
			self.client.flags['RELOAD_AU'].append(self.guild.id)

	@property
	def page(self) -> str:
		return self._page

	@page.setter
	def page(self,value) -> None:
		self.remove_confirmed = False
		self.embed.description = None
		self.embed.clear_fields()
		self.clear_items()
		match value:
			case 'main':
				self.add_items(self.custom_au_select,self.back_button,self.new_button)
				self.get_item('new_button').disabled = len(self.custom_au.keys()) >= 25
				self.update_select()
			case 'new':
				self.add_items(self.method_select,self.limit_user_select,self.back_button,self.set_button,self.regex_button,self.nsfw_button,self.case_sensitive_button,self.save_button)
				if self.selected_au:
					options = self.get_item('method_select').options
					for option in options: option.default = option.label == self.selected_au.method
					self.get_item('method_select').options = options
			case _: raise
		self._page = value

	def update_select(self):
		select = self.get_item('custom_au_select')
		if (options:=[SelectOption(label=k,description=v.get('response','').split('\n')[0][:100]) for k,v in self.custom_au.items()]):
			select.options = options
			select.placeholder = 'select an auto response'
			select.disabled = False
		else:
			select.options = [SelectOption(label='None')]
			select.placeholder = 'there are no custom auto responses'
			select.disabled = True

	def embed_au(self):
		self.embed.clear_fields()
		self.embed.add_field(name='method',value=self.selected_au.method)
		self.embed.add_field(name='match with regex',value=self.selected_au.regex)
		self.embed.add_field(name='limited to user',value=f"<@{self.selected_au.user}>" if self.selected_au.user is not None else 'None')
		self.embed.add_field(name='nsfw',value=self.selected_au.nsfw)
		self.embed.add_field(name='case sensitive',value=self.selected_au.case_sensitive)
		self.embed.add_field(name='trigger',value=self.selected_au.trigger,inline=False)
		self.embed.add_field(name='response',value=self.selected_au.response,inline=False)

	@string_select(
		custom_id='custom_au_select',row=0,
		placeholder='select an auto response')
	async def custom_au_select(self,select:Select,interaction:Interaction) -> None:
		self.remove_confirmed = False
		self.embed.description = None
		if self.custom_au.get(select.values[0],None) is None: raise ValueError(f'invalid selection `{select.values[0]}`')
		self.selected_au = AutoResponse(select.values[0],**self.custom_au.get(select.values[0]))
		self.embed_au()
		self.add_items(self.edit_button,self.remove_button)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='<',style=2,row=2,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		if self.page == 'main':
			await interaction.response.edit_message(embed=self.original_view.embed,view=self.original_view)
			self.stop()
			return
		self.page = 'main'
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='new',style=3,row=2,
		custom_id='new_button')
	async def new_button(self,button:Button,interaction:Interaction) -> None:
		self.selected_au = AutoResponse(None,method=None)
		self.page = 'new'
		self.embed_au()
		self.get_item('save_button').disabled = True
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='edit',style=1,row=2,
		custom_id='edit_button')
	async def edit_button(self,button:Button,interaction:Interaction) -> None:
		self.page = 'new'
		self.embed_au()
		self.get_item('save_button').disabled = False
		self.get_item('regex_button').style = 3 if self.selected_au.regex else 4
		self.get_item('nsfw_button').style = 3 if self.selected_au.nsfw else 4
		self.get_item('case_sensitive_button').style = 3 if self.selected_au.case_sensitive else 4
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=2,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		if self.remove_confirmed:
			if self.selected_au is None: raise ValueError('cannot remove nothing')
			self.custom_au.pop(self.selected_au.trigger)
			await self.client.db.guild(self.guild.id).data.auto_responses.custom.unset([self.selected_au.trigger.replace('.','\.')])
			await self.client.log.info(f'{self.user.name} modified custom auto responses',**{
			'author':self.user.id,
			'guild':self.guild.id,
			'trigger':self.selected_au.trigger})
			self.set_au_reload_flag()
			self.page = 'main'
		else:
			self.embed.description = 'are you sure you want to remove this auto response?\nclick remove again to remove it.'
			self.remove_confirmed = True
		await interaction.response.edit_message(embed=self.embed,view=self)

	@user_select(
		placeholder='limit to a user',row=1,
		custom_id='limit_user_select',min_values=0)
	async def limit_user_select(self,select:Select,interaction:Interaction) -> None:
		if select.values: self.selected_au.user = select.values[0].id
		else: self.selected_au.user = None
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@string_select(
		custom_id='method_select',row=0,
		placeholder='select a method',
		options=[SelectOption(label='exact',description='trigger is exactly the message'),
			SelectOption(label='contains',description='trigger anywhere within the message')])
	async def method_select(self,select:Select,interaction:Interaction) -> None:
		self.selected_au.method = select.values[0]
		for option in select.options: option.default = option.label == self.selected_au.method
		if self.selected_au.trigger is not None and self.selected_au.response is not None:
			self.get_item('save_button').disabled = False
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='set',style=1,row=2,
		custom_id='set_button')
	async def set_button(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(self,'add custom auto response',[
			InputText(label='trigger message',placeholder='cannot start with $ or contain a .',min_length=1,max_length=100,style=InputTextStyle.short,value=self.selected_au.trigger),
			InputText(label='response',placeholder='"{none}" to give no response (used for disabling a default auto response)',min_length=0,max_length=500,style=InputTextStyle.long,required=False,value=self.selected_au.response)])

		await interaction.response.send_modal(modal)
		await modal.wait()
		if modal.children[0].value.startswith('$') or '.' in modal.children[0].value:
			embed = Embed(title='an error has occurred!',color=0xff6969)
			embed.add_field(name='error',value='auto response trigger cannot start with $ or contain a .')
			await modal.interaction.response.send_message(embed=embed,ephemeral=self.client.hide(interaction))
			return
		self.selected_au.trigger = modal.children[0].value
		self.selected_au.response = modal.children[1].value if modal.children[1].value else None
		self.embed_au()
		if self.selected_au.method is not None:
			self.get_item('save_button').disabled = False
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='regex',style=4,row=2,
		custom_id='regex_button')
	async def regex_button(self,button:Button,interaction:Interaction) -> None:
		self.selected_au.regex = not self.selected_au.regex
		button.style = 3 if self.selected_au.regex else 4
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='nsfw',style=4,row=2,
		custom_id='nsfw_button')
	async def nsfw_button(self,button:Button,interaction:Interaction) -> None:
		self.selected_au.nsfw = not self.selected_au.nsfw
		button.style = 3 if self.selected_au.nsfw else 4
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='case_sensitive',style=4,row=2,
		custom_id='case_sensitive_button')
	async def case_sensitive_button(self,button:Button,interaction:Interaction) -> None:
		self.selected_au.case_sensitive = not self.selected_au.case_sensitive
		button.style = 3 if self.selected_au.case_sensitive else 4
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='save',style=3,row=3,
		custom_id='save_button',disabled=True)
	async def save_button(self,button:Button,interaction:Interaction) -> None:
		self.custom_au[self.selected_au.trigger] = self.selected_au.to_dict()
		await self.client.db.guild(self.guild.id).data.auto_responses.custom.write(self.selected_au.to_dict(),[self.selected_au.trigger])
		await self.client.log.info(f'{self.user.name} modified custom auto responses',**{
			'author':self.user.id,
			'guild':self.guild.id,
			'trigger':self.selected_au.trigger})
		self.set_au_reload_flag()
		self.page = 'main'
		await interaction.response.edit_message(embed=self.embed,view=self)