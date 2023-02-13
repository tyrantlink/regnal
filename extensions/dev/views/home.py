from discord.ui import Button,button,Select,string_select,InputText
from discord import Interaction,Embed,SelectOption,Guild,Member,InputTextStyle
from client import Client,EmptyView,CustomModal
from .commit import commit_view
from asyncio import sleep

class home_view(EmptyView):
	def __init__(self,client:Client,embed_color:int=None) -> None:
		super().__init__(timeout=0)
		self.client      = client
		self.embed       = Embed(title='dev menu',color=embed_color)
		self.embed.set_author(name=self.client.user.name,icon_url=self.client.user.avatar.url)
		self.add_items(self.option_select,self.reboot_button,self.sync_commands_button,self.echo_button,self.reload_au_button)
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
			# SelectOption(label='logs')
			])
	async def option_select(self,select:Select,interaction:Interaction) -> None:
		self.reboot_confirmation = False
		db = await self.client.db.inf('/reg/nal').read()
		match select.values[0]:
			case 'commit': view = commit_view(self,self.client,interaction.user,db.get('version'),self.embed.color)
			case 'logs':   view = None
			case _: raise ValueError('improper option selected, discord shouldn\'t allow this')
		await view.start(guild=self.client.get_guild(db.get('config',{}).get('guild')))
		await interaction.response.edit_message(view=view,embed=view.embed)

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
		modal = CustomModal(self,f'echo message',
			[InputText(label='message',max_length=2000,style=InputTextStyle.long),
			 InputText(label='delay',value='0')])
		await interaction.response.send_modal(modal)
		await modal.wait()
		await modal.interaction.response.defer(invisible=True)
		await sleep(int(modal.children[1].value))
		await interaction.channel.send(modal.children[0].value)

	@button(
		label='reload au',style=1,
		custom_id='reload_au_button')
	async def reload_au_button(self,button:Button,interaction:Interaction) -> None:
		if (reload:=self.client.flags.get('RELOAD_AU',None)) is not None and 'base' not in reload:
			self.client.flags['RELOAD_AU'].append('base')
		else:
			self.client.flags.update({'RELOAD_AU':['base']})
		await interaction.response.defer(invisible=True)