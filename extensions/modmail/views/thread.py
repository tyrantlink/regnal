from discord import Embed,Interaction,ButtonStyle,InputTextStyle,Guild,User,Member
from utils.crapi.enums import GatewayRequestType as Req
from utils.pycord_classes import SubView,MasterView
from .posted_report import ModMailPostedReportView
from discord.ui import button,Button,InputText
from utils.pycord_classes import CustomModal
from ..utils import new_modmail_message
from utils.crapi.models import Request
from discord.errors import Forbidden


class ModMailThreadView(SubView):
	def __init__(self,master:MasterView,user:User|Member,guild:Guild|None,modmail_id:str) -> None:
		super().__init__(master)
		self.user = user
		self.guild = guild
		self.modmail_id = modmail_id
		self.page = 0
		self.close_confirm = False
	
	async def __ainit__(self) -> None:
		await self.reload(True)

	async def reload(self,force_last_page:bool=False) -> None:
		self.modmail = await self.client.db.modmail(self.modmail_id)
		if self.guild is None:
			try:
				self.guild = self.client.get_guild(self.modmail.guild) or await self.client.fetch_guild(self.modmail.guild)
			except Forbidden:
				self.guild = None
		self.add_items(self.back_button,self.button_refresh,self.button_previous,self.button_next,self.button_new_message,self.button_close)
		self.pages = (len(self.modmail.messages)//5) - (0 if len(self.modmail.messages)%5 else 1)
		if force_last_page:
			self.page = self.pages
		if self.page < 0:
			self.page = 0
		if self.page > self.pages:
			self.page = self.pages
		self.get_item('button_next').disabled = self.page == self.pages
		self.get_item('button_previous').disabled = self.page == 0
		if self.modmail.closed:
			self.remove_item(self.button_new_message)
			self.remove_item(self.button_refresh)
			self.get_item('button_close').label = 'this thread has been closed'
			self.get_item('button_close').disabled = True

		user_doc = await self.client.db.user(self.user.id)
		user_doc.data.modmail_threads[self.modmail_id] = len(self.modmail.messages)
		await user_doc.save_changes()

	@property
	def embeds(self) -> list[Embed]:
		embeds = []
		for message in self.modmail.messages[5*self.page:5*(self.page+1)]:
			embed = Embed(
				description = message.content,
				color = self.master.embed_color)
			author = (
				self.guild.get_member(message.author)
				if message.author and self.guild
				else None)
			embed.set_author(
				name = author.display_name if author else 'anonymous' if self.guild else 'must be in the correct server to see author',
				icon_url = author.display_avatar.url if author else None)
			if message.attachments:
				embed.add_field(
					name = 'attachments',
					value = '\n'.join(
						f'[{attachment.filename}]({attachment.url})'
						for attachment in message.attachments))
			embeds.append(embed)
		return embeds

	@button(
		label = '🔄',
		style = ButtonStyle.gray,
		row = 2,
		custom_id = 'button_refresh')
	async def button_refresh(self,button:Button,interaction:Interaction) -> None:
		await self.reload()
		await interaction.response.edit_message(embeds=self.embeds,view=self)
	
	@button(
		label = '⬅️',
		style = ButtonStyle.gray,
		row = 2,
		custom_id = 'button_previous')
	async def button_previous(self,button:Button,interaction:Interaction) -> None:
		self.page -= 1
		await self.reload()
		await interaction.response.edit_message(embeds=self.embeds,view=self)
	
	@button(
		label = '➡️',
		style = ButtonStyle.gray,
		row = 2,
		disabled = True,
		custom_id = 'button_next')
	async def button_next(self,button:Button,interaction:Interaction) -> None:
		self.page += 1
		await self.reload()
		await interaction.response.edit_message(embeds=self.embeds,view=self)

	@button(
		label = 'new message',
		style = ButtonStyle.blurple,
		row = 3,
		custom_id = 'button_new_message')
	async def button_new_message(self,button:Button,interaction:Interaction) -> None:
		forward = str((await self.client.db.guild(self.guild.id)).attached_bot)
		if forward == 'None':
			await self.client.helpers.send_error(interaction,'this server has no attached bot, this shouldn\'t happen!')
			return
		
		modal = CustomModal(
			title = 'send a new message',
			children = [
				InputText(
					label = 'message',
					style = InputTextStyle.long,
					min_length = 1,
					max_length = 2000,
					custom_id = 'message')])

		await interaction.response.send_modal(modal)
		await modal.wait()
	
		await self.client.api.gateway_send(Request(
			req=Req.SEND_MESSAGE,
			forward=forward,
			data={
				'channel':self.modmail.thread,
				'content':modal.children[0].value}))

		await new_modmail_message(
			client = self.client,
			modmail_id = self.modmail.id,
			author = self.user if not self.modmail.anonymous else None,
			content = modal.children[0].value)

		await self.reload(True)
		await modal.interaction.response.edit_message(embeds=self.embeds,view=self)
	
	@button(
		label = 'close',
		style = ButtonStyle.red,
		row = 3,
		custom_id = 'button_close')
	async def button_close(self,button:Button,interaction:Interaction) -> None:
		if not self.close_confirm:
			self.close_confirm = True
			button.label = 'confirm close'
			button.style = ButtonStyle.red
			await interaction.response.edit_message(embeds=self.embeds,view=self)
			await interaction.followup.send('please press the button again to confirm\nonce the thread is closed no more messages can be sent',ephemeral=True)
			return
		self.modmail.closed = True
		await self.modmail.save_changes()
		thread = self.guild.get_thread(self.modmail.thread)
		if thread is None:
			await self.client.helpers.send_error(interaction,'the thread was not found, this shouldn\'t happen!')
			return
		
		await thread.send(f'this thread was closed by {"anonymous" if self.modmail.anonymous else self.user.mention}\n\nno more messages will be exchanged.\n\narchiving this thread is recommended.')
		
		view = ModMailPostedReportView(self.client)
		view.get_item('button_close').label = 'closed'
		view.get_item('button_close').disabled = True
		
		await thread.get_partial_message(thread.id).edit(view=view)
		await self.reload()
		await interaction.response.edit_message(embeds=self.embeds,view=self)