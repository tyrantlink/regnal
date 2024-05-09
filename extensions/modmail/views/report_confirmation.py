from discord import Embed,Member,Interaction,ButtonStyle,Message,InputTextStyle,ForumChannel
from .posted_report import ModMailPostedReportView
from discord.ui import button,Button,InputText
from utils.pycord_classes import CustomModal
from utils.db.documents import ModMail
from utils.pycord_classes import View
from asyncio import Event
from client import Client
from time import time


class ModMailConfirmationView(View):
	def __init__(self,client:Client,message:Message|None,reporter:Member,title:str,issue:str,allow_anonymous:bool) -> None:
		super().__init__(timeout=None)
		self.submitted = Event()
		self.client = client
		self.source_message = message
		self.reporter = reporter
		self.title = title
		self.issue_message = issue
		self.anonymous = False
		self.add_items(self.button_send_report,self.button_edit)
		if allow_anonymous:
			self.add_item(self.button_anonymous_mode)

		if self.source_message:
			self.message_proxy = Embed(
				title = f'reported message',
				description = self.source_message.content if len(self.source_message.content) < 1893 else f'{self.source_message.content[:1893]}...',
				color = 0xff6969)
			self.message_proxy.set_author(
				name = self.source_message.author.display_name,
				icon_url = self.source_message.author.display_avatar.url)
			self.message_proxy.set_footer(text=self.source_message.id)
			if self.source_message.attachments:
				self.message_proxy.add_field(
					name = 'attachments',
					value = '\n'.join(
						f'[{attachment.filename}]({attachment.url})'
						for attachment in self.source_message.attachments))

		self.reload_issue_embed()
	
	@property
	def embeds(self) -> list[Embed]:
		if self.source_message:
			return [self.message_proxy,self.issue_embed]
		return [self.issue_embed]
	
	@property
	def title_embed(self) -> Embed:
		return Embed(
			title = self.title,
			color = self.embeds[0].color)

	def reload_issue_embed(self) -> None:
		self.issue_embed = Embed(
			description = self.issue_message,
			color = 0xffff69)
		self.issue_embed.set_footer(text='modmail id: pending')
		if self.anonymous:
			self.issue_embed.set_author(
				name = 'anonymous',
				icon_url = self.client.user.display_avatar.url)
		else:
			self.issue_embed.set_author(
				name = self.reporter.display_name,
				icon_url = self.reporter.display_avatar.url)

	async def _new_modmail_document(self,interaction:Interaction) -> ModMail:
		anonymous = self.issue_embed.author.name == 'anonymous' and self.issue_embed.author.icon_url == self.client.user.display_avatar.url
		last_modmail = await self.client.db._client.modmail.find_one(
			{'guild':interaction.guild_id},projection={'_id':False,'modmail_id':True},sort=[('modmail_id',-1)])

		modmail_id = last_modmail['modmail_id'] + 1 if last_modmail else 1
		mail = ModMail(
			id=f'{interaction.guild_id}:{modmail_id}',
			guild=interaction.guild_id,
			modmail_id=modmail_id,
			anonymous=anonymous,
			title=self.title,
			message=int(self.message_proxy.footer.text) if self.source_message else None)
		mail.messages.append(
			ModMail.ModMailMessage(
				author=self.reporter.id if not anonymous else None,
				content=self.issue_message,
				timestamp=int(time())))
		await mail.insert()
		return mail

	async def new_thread(self,interaction:Interaction) -> str:
		guild_doc = await self.client.db.guild(interaction.guild_id)
		channel:ForumChannel = self.client.get_channel(guild_doc.config.modmail.channel)
		modmail = await self._new_modmail_document(interaction)
		self.issue_embed.set_footer(text=f'modmail id: {modmail.modmail_id}')
		thread = await channel.create_thread(
			name = f'{modmail.modmail_id} - {"anonymous" if self.anonymous else self.reporter.name} - {self.title}',
			content = (
				f'a [message](<{self.source_message.jump_url}>) by {self.source_message.author.mention} was reported'
				if self.source_message
				else
				f'{self.reporter.mention} reported an issue'
				if not self.anonymous
				else
				'an anonymous user reported an issue'),
			view = ModMailPostedReportView(self.client),
			embeds = self.embeds)
		guild_doc.data.modmail_threads[str(thread.id)] = modmail.modmail_id
		await guild_doc.save()
		modmail.thread = thread.id
		await modmail.save_changes()
		return modmail.modmail_id

	@button(
		label = 'send report',
		row = 1,
		style = ButtonStyle.blurple,
		custom_id = 'button_send_report')
	async def button_send_report(self,button:Button,interaction:Interaction) -> None:
		modmail_id = await self.new_thread(interaction)
		embed = Embed(
			title = 'successfully submitted report',
			description = self.client.helpers.handle_cmd_ref('you can check the status of your report using {cmd_ref[modmail]}'),
			color = await self.client.helpers.embed_color(interaction.guild.id))
		embed.set_footer(text=f'modmail id: {modmail_id}')
		user_doc = await self.client.db.user(self.reporter.id)
		user_doc.data.modmail_threads[f'{interaction.guild_id}:{modmail_id}'] = 1
		await user_doc.save()
		await interaction.response.edit_message(embed=embed,view=None)
		if not interaction.user.can_send():
			await interaction.followup.send(embed=Embed(
				title = 'warning!',
				description='i cannot send you a DM to notify you of new messages, you may have to allow direct messages from a server i\'m in.\n\nat the moment you will have to manually check {cmd_ref[modmail]} for any updates',
				color=0xffff69))
		self.stop()

	@button(
		label = 'anonymous mode',
		row = 0,
		style = ButtonStyle.red,
		custom_id = 'button_anonymous_mode')
	async def button_anonymous_mode(self,button:Button,interaction:Interaction) -> None:
		self.anonymous = not self.anonymous
		self.reload_issue_embed()
		button.style = ButtonStyle.green if self.anonymous else ButtonStyle.red
		await interaction.response.edit_message(embeds=[self.title_embed,*self.embeds],view=self)
	
	@button(
		label = 'edit',
		row = 0,
		style = ButtonStyle.blurple,
		custom_id = 'button_edit')
	async def button_edit(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(
			title = 'edit report',
			children = [
				InputText(
					label = 'title',
					style = InputTextStyle.short,
					min_length = 1,
					max_length = 50,
					custom_id = 'title'),
				InputText(
					label = 'issue',
					style = InputTextStyle.long,
					min_length = 1,
					max_length = 4000,
					custom_id = 'issue')])

		await interaction.response.send_modal(modal)
		await modal.wait()
		self.title = modal.children[0].value
		self.issue_message = modal.children[1].value
		self.reload_issue_embed()
		await modal.interaction.response.edit_message(embeds=[self.title_embed,*self.embeds],view=self)