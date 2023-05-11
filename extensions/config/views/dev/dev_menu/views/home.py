from discord.ui import Button,button,Select,string_select,InputText
from discord import Interaction,Embed,SelectOption,InputTextStyle
from utils.classes import EmptyView,CustomModal,AutoResponses
from .banning import dev_banning_view
from .commit import commit_view
from ....au import au_view
from asyncio import sleep
from client import Client

class home_view(EmptyView):
	def __init__(self,back_view:EmptyView,client:Client,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.back_view = back_view
		self.client = client
		self.embed  = Embed(title='dev menu',color=embed_color)
		self.embed.set_author(name=self.client.user.name,icon_url=self.client.user.avatar.url)
		self.add_items(
			self.back_button,
			self.option_select,
			self.reboot_button,
			self.sync_commands_button,
			self.echo_button,
			self.reload_au_button,
			self.set_nickname_button)
		self.reboot_confirmation = False

	@property
	def reboot_confirmation(self) -> None:
		return self._reboot_comf

	@reboot_confirmation.setter
	def reboot_confirmation(self,value) -> bool:
		if value:
			self.embed.description = 'click reboot again to confirm'
			self.get_item('reboot_button').label = '**reboot**'
		else:
			self.embed.description = None
			self.get_item('reboot_button').label = 'reboot'
		self._reboot_comf = value

	@string_select(
		placeholder='select a menu option',
		custom_id='option_select',row=0,options=[
			SelectOption(label='commit'),
			SelectOption(label='banning'),
			SelectOption(label='auto responses')
			])
	async def option_select(self,select:Select,interaction:Interaction) -> None:
		self.reboot_confirmation = False
		db = await self.client.db.inf('/reg/nal').read()
		match select.values[0]:
			case 'commit':  view = commit_view(self,self.client,interaction.user,db.get('version'),self.embed.color)
			case 'banning': view = dev_banning_view(self,interaction.user,self.client,self.embed.copy())
			case 'auto responses':
				au = AutoResponses(self.client.db.auto_response(0)._col,{'custom':False})
				await au.reload_au()
				view = au_view(self,interaction.user,interaction.guild,self.client,
				Embed(title=f'auto responses',color=self.embed.color),au,False)
			case _: raise ValueError('improper option selected, discord shouldn\'t allow this')
		await view.start(guild=self.client.get_guild(db.get('config',{}).get('guild')))
		await interaction.response.edit_message(view=view,embed=view.embed)

	@button(
		label='<',style=2,
		custom_id='back_button',row=1)
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.edit_message(view=self.back_view,embed=self.back_view.embed)
		self.stop()

	@button(
		label='reboot',style=4,
		custom_id='reboot_button')
	async def reboot_button(self,button:Button,interaction:Interaction) -> None:
		if self.reboot_confirmation:
			self.embed.title = f'successfully set {self.client.user.name} to False'
			self.embed.description = None
			self.embed.color = 0xff6969
			self.clear_items()
			await interaction.response.edit_message(embed=self.embed,view=self)
			exit(0)
		self.reboot_confirmation = True
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='sync commands',style=1,
		custom_id='sync_commands_button')
	async def sync_commands_button(self,button:Button,interaction:Interaction) -> None:
		self.reboot_confirmation = False
		await self.client.sync_commands()
		await interaction.response.defer(invisible=True)

	@button(
		label='echo',style=1,
		custom_id='echo_button')
	async def echo_button(self,button:Button,interaction:Interaction) -> None:
		self.reboot_confirmation = False
		modal = CustomModal(self,f'echo message',[
			InputText(label='message',max_length=2000,style=InputTextStyle.long),
			InputText(label='reply',placeholder='prepend with "p" to ping',required=False),
			InputText(label='delay',value='0'),
			InputText(label='channel',placeholder='if empty, current channel will be used',required=False)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		await modal.interaction.response.defer(invisible=True)
		channel = interaction.channel if modal.children[3].value == '' else (self.client.get_channel(int(modal.children[3].value)) or await self.client.fetch_channel(int(modal.children[3].value)))
		await sleep(int(modal.children[2].value))
		reply = None if (ref:=modal.children[1].value) == '' else await channel.fetch_message(int(ref[1:] if ref[0] == 'p' else ref))
		await channel.send(modal.children[0].value,reference=reply,mention_author=False if ref == '' else ref[0] == 'p')

	@button(
		label='reload au',style=1,
		custom_id='reload_au_button')
	async def reload_au_button(self,button:Button,interaction:Interaction) -> None:
		self.reboot_confirmation = False
		await self.client.au.reload_au()
		await interaction.response.defer(invisible=True)

	@button(
		label='set nickname',style=1,
		custom_id='set_nickname_button')
	async def set_nickname_button(self,button:Button,interaction:Interaction) -> None:
		self.reboot_confirmation = False
		modal = CustomModal(self,f'set nickname',
			[InputText(label='nickname',max_length=32,style=InputTextStyle.short,required=False)])
		await interaction.response.send_modal(modal)
		await modal.wait()
		await interaction.guild.me.edit(nick=modal.children[0].value)
		await modal.interaction.response.defer(invisible=True)