from discord import Member,Embed,Interaction,ButtonStyle,SelectOption,InputTextStyle
from discord.ui import string_select,Select,button,Button,InputText
from utils.pycord_classes import SubView,MasterView,CustomModal
from utils.db.documents.auto_response import AutoResponse
from utils.db.documents.ext.enums import AutoResponseType
from ..embed import au_info_embed,auto_response_404
from .editor import AutoResponseEditorView


class AutoResponseOverridesView(SubView):
	def __init__(self,master:MasterView,user:Member) -> None:
		super().__init__(master)
		self.user = user
		self.au:list[AutoResponse]
		self.selected:AutoResponse|None = None

	async def __ainit__(self) -> None:
		await self.reload_au()
		await self.reload_items()
		await self.reload_embed()

	async def __on_back__(self) -> None:
		await self.client.api.internal.reload_au()
		self.selected = self.client.au.get(self.selected.id).with_overrides(
			(await self.client.db.guild(self.user.guild.id)
			).data.auto_responses.overrides.get(self.selected.id,{}))
		await self.reload_au()
		await self.reload_items()
		await self.reload_embed()
		
	async def reload_au(self) -> None:
		self.au = [
			au for au in
			(
				self.client.au.au.base|
				self.client.au.au.unique(self.user.guild.id)|
				self.client.au.au.mention())
			if au.type != AutoResponseType.deleted]

	async def reload_items(self) -> None:
		self.clear_items()
		self.add_items(
			self.back_button,
			self.button_search_by_id,
			self.button_search_by_message)

		if self.selected is not None:
			self.add_items(
				self.button_edit)	

	async def reload_embed(self) -> None:
		if self.selected is None:
			self.embed = Embed(
				title = 'override auto responses',
				color = self.master.embed_color)
			return
		self.embed = await au_info_embed(self.selected,self.client,self.master.embed_color,True)

	@button(
		label = '🔎 by id',
		style = ButtonStyle.blurple,
		row = 2,
		custom_id = 'button_search_by_id')
	async def button_search_by_id(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(
			title = 'find an auto response',
			children = [
				InputText(
					label = 'auto response id',
					min_length = 2,
					max_length = 6,
					custom_id = 'au_id')])
		
		await interaction.response.send_modal(modal)

		await modal.wait()

		au_id = modal.children[0].value
		if au_id not in {au.id for au in self.au}:
			await modal.interaction.response.send_message(embed=auto_response_404,ephemeral=True)
			return
		if au_id not in (await self.client.db.user(self.user.id)).data.auto_responses.found:
			await self.client.helpers.send_error(modal.interaction,
				None,'you must have found an auto response to search for it by id!')
			return
		self.selected = self.client.au.get(au_id).with_overrides(
			(await self.client.db.guild(self.user.guild.id)).data.auto_responses.overrides.get(au_id,{}))
		await self.reload_items()
		await self.reload_embed()
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = '🔎 by message',
		style = ButtonStyle.blurple,
		row = 2,
		custom_id = 'button_search_by_message')
	async def button_search_by_message(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(
			title = 'find an auto response',
			children = [
				InputText(
					label = 'message content',
					style = InputTextStyle.long,
					min_length = 1,
					max_length = 256,
					custom_id = 'message_content'),
				InputText(
					label = 'index (when multiple found)',
					min_length = 1,
					max_length = 3,
					value = '0',
					custom_id = 'index')])

		await interaction.response.send_modal(modal)

		await modal.wait()

		message_content = modal.children[0].value
		index = int(modal.children[1].value)
		options = list(self.client.au.match(message_content,pool = self.au))

		if not options:
			await modal.interaction.response.send_message(embed=auto_response_404,ephemeral=True)
			return
		if index >= len(options):
			index = 0

		self.selected = options[index].with_overrides(
			(await self.client.db.guild(self.user.guild.id)).data.auto_responses.overrides.get(options[index].id,{}))
		await self.reload_items()
		await self.reload_embed()
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'edit',
		style = ButtonStyle.green,
		row = 2,
		custom_id = 'button_edit')
	async def button_edit(self,button:Button,interaction:Interaction) -> None:
		view = self.master.create_subview(AutoResponseEditorView,self.user,self.selected,True)
		await view.__ainit__()
		await interaction.response.edit_message(embed=view.embed,view=view)