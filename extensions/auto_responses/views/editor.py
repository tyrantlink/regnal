from discord import Member,Embed,Interaction,ButtonStyle,SelectOption,InputTextStyle
from utils.db.documents.ext.enums import AutoResponseType,AutoResponseMethod
from discord.ui import string_select,Select,button,Button,InputText
from utils.pycord_classes import SubView,MasterView,CustomModal
from utils.db.documents.auto_response import AutoResponse
from ..embed import au_info_embed
from secrets import token_hex
from typing import NamedTuple
from math import floor,ceil

DUMP_INCLUDE = {
	'method':True,
	'trigger':True,
	'response':True,
	'type':True,
	'data':
	{
	'weight',
	'chance',
	'ignore_cooldown',
	'regex',
	'nsfw',
	'case_sensitive',
	'delete_trigger'}}

class TriggerResponseSourceWeightChanceSave(NamedTuple):
	trigger:str
	response:str
	source:str|None
	weight:str
	chance:str

class AutoResponseEditorView(SubView):
	def __init__(self,master:MasterView,user:Member,auto_response:AutoResponse|None,override:bool=False) -> None:
		super().__init__(master)
		self.user = user
		self.override = override
		self.au = (
			auto_response.model_copy()
			if auto_response is not None else
			AutoResponse(
				id='unset',
				method=AutoResponseMethod.exact,
				trigger='None',
				response='None',
				type=AutoResponseType.text))

		if not self.override:
			self.au.data.custom = True
			self.au.data.guild = self.user.guild.id

		self.button_help = Button(
			label = 'help',
			style = ButtonStyle.link,
			url = 'https://docs.regn.al/extensions/auto%20responses/auto%20response%20attributes',
			row = 4)

		self.trswc_modal_save = TriggerResponseSourceWeightChanceSave(
			trigger = '' if self.au.trigger == 'None' else self.au.trigger,
			response = '' if self.au.response == 'None' else self.au.response,
			source = self.au.data.source,
			weight = str(self.au.data.weight),
			chance = str(self.au.data.chance))
		
	async def __ainit__(self) -> None:
		if self.override:
			guild_doc = await self.client.db.guild(self.user.guild.id)
			self.au = self.au.with_overrides(guild_doc.data.auto_responses.overrides.get(self.au.id,{}))
		await self.reload()

	async def reload(self) -> None:
		await self.reload_embed()
		await self.reload_items()

	async def reload_embed(self) -> None:
		self.embed = Embed(
			title = f'override auto response {self.au.id}' if self.override else 'new custom auto response',
			color = self.master.embed_color)
		self.embed.add_field(
			name = 'trigger',inline = True,
			value = self.au.trigger)
		self.embed.add_field(
			name = 'response',inline = False,
			value = self.au.response)
		if not self.override:
			self.embed.add_field(
				name = 'source',inline = False,
				value = self.client.helpers.handle_cmd_ref(self.au.data.source) if self.au.data.source else None)
		self.embed.add_field(
			name = 'method',inline = True,
			value = self.au.method.name)
		self.embed.add_field(
			name = 'weight',inline = True,
			value = self.au.data.weight)
		self.embed.add_field(
			name = 'chance',inline = True,
			value = f'{self.au.data.chance}%')
		self.embed.add_field(
			name = 'ignore cooldown',inline = True,
			value = self.au.data.ignore_cooldown)
		self.embed.add_field(
			name = 'regex matching',inline = True,
			value = self.au.data.regex)
		self.embed.add_field(
			name = 'nsfw',inline = True,
			value = self.au.data.nsfw)
		self.embed.add_field(
			name = 'case sensitive',inline = True,
			value = self.au.data.case_sensitive)
		self.embed.add_field(
			name = 'delete trigger',inline = True,
			value = self.au.data.delete_trigger)

	async def reload_items(self) -> None:
		self.clear_items()
		self.add_item(self.back_button)
		self.get_item('back_button').row = 1
		self.remove_item(self.back_button)

		for item_name in ['ignore_cooldown','regex','nsfw','case_sensitive','delete_trigger']:
			self.add_item(getattr(self,f'button_{item_name}'))
			item = self.get_item(f'button_{item_name}')
			item.style = (
				ButtonStyle.green
				if getattr(self.au.data,item_name)
				else ButtonStyle.red)

		self.add_items(
			self.back_button,
			self.select_method,
			self.button_trigger_response_source_weight_chance,
			self.button_save,
			self.button_help)
		self.get_item('button_trigger_response_source_weight_chance'
			).label = f'set trigger, response, {"" if self.override else "source, "}weight, and chance'

	@string_select(
		placeholder = 'method',
		custom_id = 'select_method',
		row = 0,
		options = [
			SelectOption(
				label = method.name,
				value = str(method.value),
				default = not method.value) # default is exact[0]
			for method in AutoResponseMethod])
	async def select_method(self,select:Select,interaction:Interaction) -> None:
		self.au.method = AutoResponseMethod(int(select.values[0]))
		for option in select.options:
			option.default = option.value == select.values[0]
		await self.reload_embed()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'unset',
		style = ButtonStyle.blurple,
		row = 1,
		custom_id = 'button_trigger_response_source_weight_chance')
	async def button_trigger_response_source_weight_chance(self,button:Button,interaction:Interaction) -> None:
		modal = CustomModal(
			title = f'set trigger, response, {"" if self.override else "source, "}weight, chance',
			children = [
				InputText(
					label = 'trigger',
					custom_id = 'input_trigger',
					placeholder = 'trigger',
					min_length = 1,
					max_length = 384,
					value = self.trswc_modal_save.trigger,
					required = True),
				InputText(
					label = 'response',
					style = InputTextStyle.long,
					custom_id = 'input_response',
					placeholder = 'response',
					min_length = 1,
					max_length = 1024,
					value = self.trswc_modal_save.response,
					required = True),
				InputText(
					label = 'source',
					style = InputTextStyle.long,
					custom_id = 'input_source',
					placeholder = 'source',
					max_length = 1024,
					value = self.trswc_modal_save.source,
					required = False),
				InputText(
					label = 'weight',
					custom_id = 'input_weight',
					placeholder = 'weight',
					min_length = 1,
					max_length = 6,
					value = self.trswc_modal_save.weight,
					required = True),
				InputText(
					label = 'chance',
					custom_id = 'input_chance',
					placeholder = 'chance',
					min_length = 1,
					max_length = 6,
					value = self.trswc_modal_save.chance,
					required = True)])
		if self.override:
			modal.children.pop(2)

		await interaction.response.send_modal(modal)
		await modal.wait()
		
		trigger  = modal.children[0].value
		response = modal.children[1].value
		source   = modal.children[2].value if not self.override else None
		weight   = modal.children[3-int(self.override)].value
		chance   = modal.children[4-int(self.override)].value
		self.trswc_modal_save = TriggerResponseSourceWeightChanceSave(
			trigger = trigger,
			response = response,
			source = source,
			weight = weight,
			chance = chance)
		# validation
		fail_reasons = []
		try: int(weight)
		except ValueError: fail_reasons.append('weight must be an number')
		try:
			float(chance)
			if not 0 <= float(chance) <= 100: fail_reasons.append('chance must be between 0 and 100')
		except ValueError: fail_reasons.append('chance must be a number')
		if fail_reasons:
			await modal.interaction.response.defer()
			try: raise ValueError('\n'.join(fail_reasons))
			except ValueError as e:
				e.add_note('suppress')
				raise e
		# end validation
		self.au.trigger = trigger
		self.au.response = response
		if not self.override: self.au.data.source = source
		self.au.data.weight = int(weight)
		self.au.data.chance = float(chance)
		await self.reload()
		await modal.interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'ignore cooldown',
		style = ButtonStyle.secondary,
		row = 2,
		custom_id = 'button_ignore_cooldown')
	async def button_ignore_cooldown(self,button:Button,interaction:Interaction) -> None:
		self.au.data.ignore_cooldown = not self.au.data.ignore_cooldown
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'regex matching',
		style = ButtonStyle.secondary,
		row = 2,
		custom_id = 'button_regex')
	async def button_regex(self,button:Button,interaction:Interaction) -> None:
		self.au.data.regex = not self.au.data.regex
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'nsfw',
		style = ButtonStyle.secondary,
		row = 2,
		custom_id = 'button_nsfw')
	async def button_nsfw(self,button:Button,interaction:Interaction) -> None:
		self.au.data.nsfw = not self.au.data.nsfw
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'case sensitive',
		style = ButtonStyle.secondary,
		row = 3,
		custom_id = 'button_case_sensitive')
	async def button_case_sensitive(self,button:Button,interaction:Interaction) -> None:
		self.au.data.case_sensitive = not self.au.data.case_sensitive
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'delete trigger',
		style = ButtonStyle.secondary,
		row = 3,
		custom_id = 'button_delete_trigger')
	async def button_delete_trigger(self,button:Button,interaction:Interaction) -> None:
		self.au.data.delete_trigger = not self.au.data.delete_trigger
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	async def save_override(self,interaction:Interaction) -> None:
		guild_doc = await self.client.db.guild(self.user.guild.id)
		original_au = self.client.au.get(self.au.id)
		if original_au is None:
			await interaction.response.send_message('auto response not found',ephemeral=True)
			return

		original_au_data:dict = original_au.model_dump(include=DUMP_INCLUDE)
		override_data:dict = self.au.model_dump(include=DUMP_INCLUDE)
		#! maybe try to find a better way of doing this before release because it's yucky
		for key in original_au_data:
			if original_au_data[key] == override_data[key]:
				override_data.pop(key)
		if override_data.get('data',False):
			for key in original_au_data['data']:
				if original_au_data['data'][key] == override_data['data'][key]:
					override_data['data'].pop(key)
		
		guild_doc.data.auto_responses.overrides[self.au.id] = override_data
		await guild_doc.save() # has to be hard save because messing with dictionaries doesn't count as a change

	@button(
		label = 'save',
		style = ButtonStyle.green,
		row = 4,
		custom_id = 'button_save')
	async def button_save(self,button:Button,interaction:Interaction) -> None:
		if self.override:
			await self.save_override(interaction)
			await self.back_button.callback(interaction)
			return
		if self.au.id == 'unset':
			self.au = await self.client.api.au.new(self.au)
		await self.au.save()
		await self.back_button.callback(interaction)
