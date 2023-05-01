from discord.ui import Button,button,Select,string_select,user_select,InputText
from discord import Interaction,Embed,SelectOption,InputTextStyle,Guild,Member
from utils.classes import EmptyView,CustomModal,AutoResponse
from .alt_responses import alt_responses_view
from .followups import followups_view
from client import Client


class au_view(EmptyView):
	def __init__(self,back_view:EmptyView,user:Member,guild:Guild,client:Client,embed:Embed,au:dict,base:bool) -> None:
		super().__init__(timeout=0)
		self.back_view = back_view
		self.user    = user
		self.client  = client
		self.guild   = guild
		self.embed   = embed
		self.au      = au
		self.base    = base
		self.au_page = 1
		self.selected_au:AutoResponse = None
		self.past_au:AutoResponse = None
		self.page = 'main'

	async def start(self,**kwargs) -> None: pass

	def set_au_reload_flag(self) -> None:
		if self.client.flags.get('RELOAD_AU',None) is None: self.client.flags.update({'RELOAD_AU':[]})
		if self.base and 'base' not in self.client.flags.get('RELOAD_AU'): self.client.flags['RELOAD_AU'].append('base')
		elif self.guild.id not in self.client.flags.get('RELOAD_AU'): self.client.flags['RELOAD_AU'].append(self.guild.id)

	def set_done(self,bool:bool) -> None:
		self.get_item('save_button').disabled = bool
		self.get_item('alt_responses_button').disabled = bool
		self.get_item('followups_button').disabled = bool

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
				self.add_items(self.au_select,self.back_button,self.new_button)
				if self.base: self.add_items(self.previous_button,self.next_button)
				else: self.get_item('new_button').disabled = len(self.au.keys()) >= 25
				self.update_select()
			case 'new':
				self.add_items(self.method_select,self.limit_user_select,self.back_button,self.set_button,self.regex_button,self.nsfw_button,self.case_sensitive_button,self.save_button,self.alt_responses_button,self.followups_button)
				if self.base: self.add_items(self.file_button)
				if self.selected_au:
					options = self.get_item('method_select').options
					for option in options: option.default = option.label == self.selected_au.method
					self.get_item('method_select').options = options
					self.get_item('alt_responses_button').disabled = bool(self.selected_au.followups)
					self.get_item('followups_button').disabled = bool(self.selected_au.alt_responses)
			case _: raise
		self._page = value

	def update_select(self):
		select = self.get_item('au_select')
		if (options:=[SelectOption(label=k,description=None if v.get('response',None) is None else v.get('response','').split('\n')[0][:100]) for k,v in self.au.items()][25*self.au_page-25:25*self.au_page]):
			select.options = options
			select.placeholder = 'select an auto response'
			select.disabled = False
		else:
			select.options = [SelectOption(label='None')]
			select.placeholder = 'there are no auto responses'
			select.disabled = True

	def embed_au(self):
		self.embed.clear_fields() 
		self.embed.add_field(name='method',value=self.selected_au.method,inline=False)
		self.embed.add_field(name='match with regex',value=self.selected_au.regex)
		self.embed.add_field(name='limited to user',value=f"<@{self.selected_au.user}>" if self.selected_au.user is not None else 'None')
		if self.base:
			guild = self.client.get_guild(int(self.selected_au.guild)) if self.selected_au.guild else None
			self.embed.add_field(name='limited to guild',value=guild.name if guild is not None else 'Unknown' if self.selected_au.guild else 'None')
		self.embed.add_field(name='nsfw',value=self.selected_au.nsfw)
		self.embed.add_field(name='case sensitive',value=self.selected_au.case_sensitive)
		if self.base: self.embed.add_field(name='file',value=self.selected_au.file)
		self.embed.add_field(name='trigger',value=self.selected_au.trigger,inline=False)
		self.embed.add_field(name='response',value=self.selected_au.response,inline=False)
		self.embed.add_field(name='has alt responses or followups',value='alt responses' if bool(self.selected_au.alt_responses) else 'followups' if bool(self.selected_au.followups) else 'No',inline=False)		

	@string_select(
		custom_id='au_select',row=0,
		placeholder='select an auto response')
	async def au_select(self,select:Select,interaction:Interaction) -> None:
		self.remove_confirmed = False
		self.embed.description = None
		if self.au.get(select.values[0],None) is None: raise ValueError(f'invalid selection `{select.values[0]}`')
		self.selected_au = AutoResponse(select.values[0],**self.au.get(select.values[0]))
		self.past_au = AutoResponse(select.values[0],**self.au.get(select.values[0]))
		self.add_items(self.edit_button,self.remove_button)
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='<',style=2,row=2,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		if self.page == 'main':
			await interaction.response.edit_message(embed=self.back_view.embed,view=self.back_view)
			self.stop()
			return
		self.page = 'main'
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='new',style=3,row=2,
		custom_id='new_button')
	async def new_button(self,button:Button,interaction:Interaction) -> None:
		self.selected_au = AutoResponse(None,method=None)
		self.past_au = AutoResponse(None,method=None)
		self.page = 'new'
		self.embed_au()
		self.set_done(True)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='edit',style=1,row=2,
		custom_id='edit_button')
	async def edit_button(self,button:Button,interaction:Interaction) -> None:
		self.page = 'new'
		self.embed_au()
		self.set_done(False)
		self.get_item('regex_button').style = 3 if self.selected_au.regex else 4
		self.get_item('nsfw_button').style = 3 if self.selected_au.nsfw else 4
		self.get_item('case_sensitive_button').style = 3 if self.selected_au.case_sensitive else 4
		if self.base: self.get_item('file_button').style = 3 if self.selected_au.file else 4
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='remove',style=4,row=2,
		custom_id='remove_button')
	async def remove_button(self,button:Button,interaction:Interaction) -> None:
		if self.remove_confirmed:
			if self.selected_au is None: raise ValueError('cannot remove nothing')
			self.au.pop(self.selected_au.trigger)
			if self.base: await self.client.db.inf('/reg/nal').auto_responses.unset([self.selected_au.trigger.replace('.','\.')])
			await self.client.db.guild(self.guild.id).data.auto_responses.custom.unset([self.selected_au.trigger.replace('.','\.')])
			await self.client.log.info(f'{self.user.name} modified {"base" if self.base else "custom"} auto responses',
				author=self.user.id,
				trigger=self.selected_au.trigger)
			self.set_au_reload_flag()
			self.page = 'main'
			if self.base: await self.client.db.user(0)._col.update_many({'data.au':self.selected_au.trigger},{'$pull':{'data.au':self.selected_au.trigger}})
		else:
			self.embed.description = 'are you sure you want to remove this auto response?\nclick remove again to remove it.'
			self.remove_confirmed = True
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='previous page',style=2,row=3,
		custom_id='previous_button',disabled=True)
	async def previous_button(self,button:Button,interaction:Interaction) -> None:
		self.au_page -= 1
		self.update_select()
		button.disabled = self.au_page == 1
		self.get_item('next_button').disabled = len(self.au) <= self.au_page*25
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='next page',style=2,row=3,
		custom_id='next_button')
	async def next_button(self,button:Button,interaction:Interaction) -> None:
		self.au_page += 1
		self.update_select()
		self.get_item('previous_button').disabled = self.au_page == 1
		button.disabled = len(self.au) <= self.au_page*25
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
			self.set_done(False)
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='set',style=1,row=2,
		custom_id='set_button')
	async def set_button(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(self,'add auto response',[
			InputText(label='trigger message',placeholder='cannot start with $ or contain a .',min_length=1,max_length=100,style=InputTextStyle.short,value=self.selected_au.trigger),
			InputText(label='response',placeholder='leave blank to give no response (used for disabling a default auto response)',min_length=0,max_length=500,style=InputTextStyle.long,required=False,value=self.selected_au.response)])
		if self.base: modal.add_item(InputText(label='limit guild',placeholder='guild id',min_length=0,max_length=30,style=InputTextStyle.short,required=False,value=self.selected_au.guild))
		await interaction.response.send_modal(modal)
		await modal.wait()
		if modal.children[0].value.startswith('$') or '.' in modal.children[0].value:
			embed = Embed(title='an error has occurred!',color=0xff6969)
			embed.add_field(name='error',value='auto response trigger cannot start with $ or contain a .')
			await modal.interaction.response.send_message(embed=embed,ephemeral=self.client.hide(interaction))
			return
		self.selected_au.trigger = modal.children[0].value
		self.selected_au.response = modal.children[1].value if modal.children[1].value else None
		if self.base: self.selected_au.guild = modal.children[2].value if modal.children[2].value else None
		self.embed_au()
		if self.selected_au.method is not None:
			self.set_done(False)
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
		label='file',style=4,row=3,
		custom_id='file_button')
	async def file_button(self,button:Button,interaction:Interaction) -> None:
		self.selected_au.file = not self.selected_au.file
		button.style = 3 if self.selected_au.file else 4
		self.embed_au()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='alt responses',style=1,row=3,
		custom_id='alt_responses_button')
	async def alt_responses_button(self,button:Button,interaction:Interaction) -> None:
		view = alt_responses_view(self)
		await interaction.response.edit_message(embed=view.embed,view=view)

	@button(
		label='followups',style=1,row=3,
		custom_id='followups_button')
	async def followups_button(self,button:Button,interaction:Interaction) -> None:
		view = followups_view(self)
		await interaction.response.edit_message(embed=view.embed,view=view)

	@button(
		label='save',style=3,row=4,
		custom_id='save_button',disabled=True)
	async def save_button(self,button:Button,interaction:Interaction) -> None:
		if self.past_au.trigger is not None and self.selected_au.trigger != self.past_au.trigger: self.au.pop(self.past_au.trigger)
		self.au[self.selected_au.trigger] = self.selected_au.to_dict()
		if self.base: await self.client.db.inf('/reg/nal').auto_responses.write(self.selected_au.to_dict(False),[self.selected_au.trigger])
		else: await self.client.db.guild(self.guild.id).data.auto_responses.custom.write(self.selected_au.to_dict(),[self.selected_au.trigger])
		await self.client.log.info(f'{self.user.name} modified {"base" if self.base else "custom"} auto responses',
			author=self.user.id,
			trigger=self.selected_au.trigger)
		self.set_au_reload_flag()
		self.au = await self.client.db.inf('/reg/nal').auto_responses.read()
		self.page = 'main'
		await interaction.response.edit_message(embed=self.embed,view=self)