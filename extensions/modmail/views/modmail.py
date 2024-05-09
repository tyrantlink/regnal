from discord import Embed,Interaction,ButtonStyle,InputTextStyle,Guild,User,Member
from .report_confirmation import ModMailConfirmationView
from utils.pycord_classes import SubView,MasterView
from discord.ui import button,Button,InputText
from utils.pycord_classes import CustomModal
from .inbox import ModMailInboxView


class ModMailView(SubView):
	def __init__(self,master:MasterView,user:User|Member,guild:Guild|None) -> None:
		super().__init__(master)
		self.user = user
		self.guild = guild
		self.add_item(self.button_inbox)
		if self.guild:
			self.add_item(self.button_new_message)
		self.embed = Embed(
			title = 'modmail',
			description = 'check your modmail inbox or send a new message',
			color = self.master.embed_color)

	@button(
		label = 'inbox',
		style = ButtonStyle.blurple,
		custom_id = 'button_inbox')
	async def button_inbox(self,button:Button,interaction:Interaction) -> None:
		view = self.master.create_subview(ModMailInboxView,user=self.user,guild=self.guild)
		await view.__ainit__()
		await interaction.response.edit_message(embed=view.embed,view=view)
	
	@button(
		label = 'new message',
		style = ButtonStyle.blurple,
		custom_id = 'new_message')
	async def button_new_message(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(
			title = 'send a modmail message',
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
		guild_doc = await self.client.db.guild(interaction.guild.id)

		confirmation_view = ModMailConfirmationView(
			client=self.client,
			message=None,
			reporter=interaction.user,
			title=modal.children[0].value,
			issue=modal.children[0].value,
			allow_anonymous=guild_doc.config.modmail.allow_anonymous)

		await modal.interaction.response.send_message(
			embeds=[confirmation_view.title_embed,*confirmation_view.embeds],
			view=confirmation_view,
			ephemeral=True)