from discord import Member,Embed,Interaction,ButtonStyle,InputTextStyle
from utils.db.documents import AutoResponse,User as UserDoc
from ..embed import au_info_embed,auto_response_404
from utils.pycord_classes import View,CustomModal
from discord.ui import button,Button,InputText
from client import Client

class AutoResponseBrowserView(View):
	def __init__(self,client:Client,user:Member) -> None:
		super().__init__()
		self.client = client
		self.user = user
		self.au_found_dict:dict[str,list[str]]
		self.au_found:list[str] = []
		self.au_index:int = 0
		self.au:AutoResponse = None
		self.guild_overrides:dict = {}
		self.with_overrides:bool = False

	def _au_sort(self,auto_responses:list[str]) -> list[str]:
		return sorted(auto_responses,key=lambda au_id:int(au_id[1:]))

	async def __ainit__(self) -> None:
		user_doc = await self.client.db.user(self.user.id)
		self.au_found_dict = {
			'base': self._au_sort([a for a in user_doc.data.auto_responses.found if a[0] == 'b']),
			'custom': self._au_sort([a for a in user_doc.data.auto_responses.found if a[0] == 'c']),
			'unique': self._au_sort([a for a in user_doc.data.auto_responses.found if a[0] == 'u']),
			'mention': self._au_sort([a for a in user_doc.data.auto_responses.found if a[0] == 'm']),
			'personal': self._au_sort([a for a in user_doc.data.auto_responses.found if a[0] == 'p']),
			'script': self._au_sort([a for a in user_doc.data.auto_responses.found if a[0] == 's'])
		}
		self.au_found = [au for category in self.au_found_dict.values() for au in category]
		print(self.au_found)

		# remove any auto responses that have been deleted
		self.au_found = [
			a for a in self.au_found
			if (
				au:=self.client.au.get(a)
			)]

		self.guild_overrides = (await self.client.db.guild(self.user.guild.id)).data.auto_responses.overrides

		if not self.au_found:
			self.embed = Embed(
				title = 'you haven\'t found any auto responses yet!',
				description = 'you have to trigger an auto response to find it!',
				color = 0xff6969)
			return

		await self.reload(user_doc)

	async def reload(self,user_doc:UserDoc|None=None) -> None:
		self.au = self.client.au.get(self.au_found[self.au_index])
		#? probably unnecessary, but no leaks pls
		if self.au.id not in self.au_found: 
			self.stop()
			return
		user_doc = user_doc or await self.client.db.user(self.user.id)
		await self.reload_embed(user_doc)
		await self.reload_items(user_doc)

	async def reload_embed(self,user_doc:UserDoc|None=None) -> None:
		user_doc = user_doc or await self.client.db.user(self.user.id)
		self.embed = await au_info_embed(
			auto_response = self.au,
			client = self.client,
			embed_color = await self.client.helpers.embed_color(
				self.user.guild.id
				if getattr(self.user,'guild',None)
				else None),
			extra_info = user_doc.config.general.developer_mode)
		if self.guild_overrides.get(self.au.id,{}):
			self.embed.set_author(
				name = f'!! this server has custom overrides !!')

	async def reload_items(self,user_doc:UserDoc|None=None) -> None:
		self.clear_items()
		user_doc = user_doc or await self.client.db.user(self.user.id)
		self.add_item(self.button_previous)
		match self.au.id in user_doc.data.auto_responses.disabled:
			case True: self.add_item(self.button_enable)
			case False: self.add_item(self.button_disable)
		self.add_items(
			self.button_next,
			self.button_search_by_id,
			self.button_search_by_message)
		if self.guild_overrides.get(self.au.id,{}):
			self.add_item(self.button_with_overrides)
			self.get_item('button_with_overrides').style = ButtonStyle.green if self.with_overrides else ButtonStyle.red

	@button(
		label = '<',
		row = 0,
		style = ButtonStyle.grey,
		custom_id = 'button_previous')
	async def button_previous(self,button:Button,interaction:Interaction) -> None:
		self.with_overrides = False
		self.au_index -= 1
		if self.au_index < 0: self.au_index = len(self.au_found)-1
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = '>',
		row = 0,
		style = ButtonStyle.grey,
		custom_id = 'button_next')
	async def button_next(self,button:Button,interaction:Interaction) -> None:
		self.with_overrides = False
		self.au_index += 1
		if self.au_index >= len(self.au_found): self.au_index = 0
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'enable',
		row = 0,
		style = ButtonStyle.green,
		custom_id = 'button_enable')
	async def button_enable(self,button:Button,interaction:Interaction) -> None:
		user_doc = await self.client.db.user(self.user.id)
		try: user_doc.data.auto_responses.disabled.remove(self.au.id)
		except ValueError: pass
		await user_doc.save_changes()
		await self.reload(user_doc)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'disable',
		row = 0,
		style = ButtonStyle.red,
		custom_id = 'button_disable')
	async def button_disable(self,button:Button,interaction:Interaction) -> None:
		user_doc = await self.client.db.user(self.user.id)
		user_doc.data.auto_responses.disabled.append(self.au.id)
		await user_doc.save_changes()
		await self.reload(user_doc)
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = '🔎 by id',
		row = 1,
		style = ButtonStyle.blurple,
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
		if au_id not in self.au_found:
			await modal.interaction.response.send_message(embed=auto_response_404,ephemeral=True)
			return
		self.au_index = self.au_found.index(au_id)
		await self.reload()
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = '🔍 by message',
		row = 1,
		style = ButtonStyle.blurple,
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
		options = self.client.au.match(
			message_content,
			self.guild_overrides,
			pool = [
				au for au in
				[
					*self.client.au.au.base,
					*self.client.au.au.custom(self.user.guild.id),
					*self.client.au.au.unique(self.user.guild.id),
					*self.client.au.au.mention(),
					*self.client.au.au.personal(self.user.id),
					*self.client.au.au.scripted(
						(await self.client.db.guild(self.user.guild.id)).data.auto_responses.imported_scripts)]])

		if not options:
			await modal.interaction.response.send_message(embed=auto_response_404,ephemeral=True)
			return
		if index >= len(options):
			index = 0
		au = options[index]
		if au.id not in self.au_found:
			await modal.interaction.response.send_message(embed=auto_response_404,ephemeral=True)
			return

		self.au_index = self.au_found.index(au.id)
		await self.reload()
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		row = 0,
		label = 'with overrides',
		style = ButtonStyle.red,
		custom_id = 'button_with_overrides')
	async def button_with_overrides(self,button:Button,interaction:Interaction) -> None:
		self.with_overrides = not self.with_overrides
		if self.with_overrides:
			self.au = self.au.with_overrides(self.guild_overrides.get(self.au.id,{}))
		else:
			self.au = self.client.au.get(self.au_found[self.au_index])
		await self.reload_items()
		await self.reload_embed()
		await interaction.response.edit_message(embed=self.embed,view=self)
