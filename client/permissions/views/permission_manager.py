from discord import Member,Embed,Interaction,Role,ButtonStyle,InputTextStyle
from discord.ui import mentionable_select,Select,button,Button,InputText
from utils.pycord_classes import MasterView,SubView,CustomModal
from utils.db.documents import Guild as GuildDoc


class PermissionManagerView(SubView):
	def __init__(self,master:MasterView,user:Member) -> None:
		super().__init__(master)
		self.user = user
		self.selected_value:Member|Role|None = None

	async def __ainit__(self) -> None:
		await self.reload_embed()
		await self.reload_items()

	@property
	def value_id(self) -> str:
		if self.selected_value is None: return None
		return '@everyone' if self.selected_value == self.user.guild.default_role else str(self.selected_value.id)

	async def reload_embed(self,guild_doc:GuildDoc|None=None) -> None:
		guild_doc = guild_doc or await self.client.db.guild(self.user.guild.id)
		self.embed = Embed(
			title = 'permission manager',
			color = self.master.embed_color)
		if self.selected_value is not None:
			permissions = '\n'.join(guild_doc.data.permissions.get(self.value_id,[]))

			self.embed.add_field(
				name = f'selected {"user" if isinstance(self.selected_value,Member) else "role"}',
				value = self.selected_value.mention,
				inline = False)

			self.embed.add_field(
				name = 'permissions',
				value = f'```\n{permissions}\n```' if permissions else 'None',
				inline = False)

			return

		self.embed.description = '\n'.join({
			'@everyone'
			if i == '@everyone' else
			f'<@&{i}>'
			if self.user.guild.get_role(int(i)) is not None else
			f'<@{i}>'
			for i in guild_doc.data.permissions
			if guild_doc.data.permissions[i]
		}) or 'None'

	async def reload_items(self) -> None:
		self.add_items(
			self.back_button,
			self.mentionable_select,
			self.button_everyone,
			self.button_list_permissions)
		if self.selected_value is not None:
			self.add_items(
				self.button_modify,
				self.button_remove_all)

	async def log(self,added:set|None=None,removed:set|None=None) -> None:
		if not added and not removed: return
		guild_doc = await self.client.db.guild(self.user.guild.id)
		if (
			guild_doc.config.logging.enabled and
			guild_doc.config.logging.channel and
			guild_doc.config.logging.log_commands
		):
			channel = self.user.guild.get_channel(int(guild_doc.config.logging.channel))
			if channel is None:
				return
			embed = Embed(
				title = 'permissions modified!',
				color = 0xffff69)
			embed.set_author(name=self.user.name,icon_url=self.user.avatar.url)
			if added:
				added = '\n'.join(added)
				embed.add_field(
					name = 'added permissions',
					value = f"```\n{added}\n```",
					inline = False)
			if removed:
				removed = '\n'.join(removed)
				embed.add_field(
					name = 'removed permissions',
					value = f"```\n{removed}\n```",
					inline = False)
			if not embed.fields:
				return
			await channel.send(embed=embed)

	@mentionable_select(
		placeholder = 'select a user/role to manage',
		row = 0,
		min_values = 0,
		custom_id = 'mentionable_select')
	async def mentionable_select(self,select:Select,interaction:Interaction) -> None:
		if select.values and select.values[0].id == self.user.id:
			await self.client.helpers.send_error(interaction,'you cannot manage your own permissions!')
			return

		self.selected_value = select.values[0] if select.values else None
		await self.reload_embed()
		await self.reload_items()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = '@everyone',
		row = 2,
		style = ButtonStyle.blurple,
		custom_id = 'button_everyone')
	async def button_everyone(self,button:Button,interaction:Interaction) -> None:
		self.selected_value = self.user.guild.default_role
		await self.reload_embed()
		await self.reload_items()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label = 'modify',
		row = 2,
		style = ButtonStyle.green,
		custom_id = 'button_modify')
	async def button_modify(self,button:Button,interaction:Interaction) -> None:
		guild_doc = await self.client.db.guild(self.user.guild.id)
		modal = CustomModal(
			f'edit permissions',
			[
				InputText(
					label = 'permissions',
					placeholder = 'permissions, separated by new lines, e.g.\ntts.ban\nauto_responses.*',
					style = InputTextStyle.long,
					required = False,
					value = '\n'.join(guild_doc.data.permissions.get(self.value_id,[])))])

		await interaction.response.send_modal(modal)
		old_permissions = set(guild_doc.data.permissions.get(self.value_id,[]))
		await modal.wait()
		new_value = [
			permission.lower().strip()
			for permission in
			modal.children[0].value.split('\n')
		] if modal.children[0].value else []
		for permission in new_value:
			if not self.client.permissions.matcher(permission[1:] if permission.startswith('!') else permission):
				await self.client.helpers.send_error(interaction,
					f'the given permission `{permission}` does not match any existing permissions')
				return
			user_permissions = await self.client.permissions.user(self.user,self.user.guild)
			permission_diff = self.client.permissions.matcher(permission) - user_permissions
			if (
				not self.user.guild_permissions.administrator and
				permission_diff
			):
				permission_diff_print = '\n'.join(sorted(permission_diff))
				await self.client.helpers.send_error(interaction,
					f'''the matcher `{permission}` matches permissions that you don\'t have!
									please ask an admin to make these changes, or give you the following permissions:
									```\n{permission_diff_print}\n```
					 '''.replace('\t','')[:-2])
				return

		if new_value:
			guild_doc.data.permissions[self.value_id] = new_value
			await guild_doc.save_changes()
		else:
			guild_doc.data.permissions.pop(self.value_id,None)
			#? guild_doc.save_changes() doesn't work when removing a key from a dict, so we have to use this instead
			await GuildDoc.find_one({'_id':guild_doc.id}).update({'$set':{'data.permissions':guild_doc.data.permissions}})
		await self.reload_embed(guild_doc)
		await modal.interaction.response.edit_message(embed=self.embed,view=self)
		await self.log(
			added = set(new_value) - old_permissions,
			removed = old_permissions - set(new_value))

	@button(
		label = 'remove all',
		row = 2,
		style = ButtonStyle.red,
		custom_id = 'button_remove_all')
	async def button_remove_all(self,button:Button,interaction:Interaction) -> None:
		guild_doc = await self.client.db.guild(self.user.guild.id)
		removed = guild_doc.data.permissions.pop(self.value_id,None)
		#? guild_doc.save_changes() doesn't work when removing a key from a dict, so we have to use this instead
		await GuildDoc.find_one({'_id':guild_doc.id}).update({'$set':{'data.permissions':guild_doc.data.permissions}})
		await self.reload_embed(guild_doc)
		await interaction.response.edit_message(embed=self.embed,view=self)
		await self.log(removed = set(removed) if removed else None)

	@button(
		label = 'permission list and tutorial',
		row = 3,
		style = ButtonStyle.grey,
		custom_id = 'button_list_permissions')
	async def button_list_permissions(self,button:Button,interaction:Interaction) -> None:
		permissions = '\n'.join(sorted(self.client.permissions.permissions))
		description = '''how to use permissions
									- permissions are case insensitive
									- permissions are set using matchers, for example, if a user has the permission `tts.*`, they will have all permissions that start with `tts.`
									- if a user has the permission `*`, they will have all permissions
									- if a user has the discord permission `administrator`, they will have all permissions
									- if a user has a single permission, for example, `general.embed_color`, they will only be able to see that option
									- if a user has a category permission, for example, `general`, they will be able to see all options, but only modify the ones they have permissions for
									- prefix a permission with `!` to negate it, for example, `!tts.ban` will remove the permission `tts.ban`
									- negated permissions will be applied after all other permissions
									- for example, if a user has the permission `tts.*` and the permission `!tts.ban`, they will have all tts permissions except `tts.ban`
									'''.replace('\t','')[:-1]
		await interaction.response.send_message(
			embed = Embed(
				title = 'all permissions',
				description = f'```\n{permissions}\n```\n{description}',
				color = self.master.embed_color),
			ephemeral = True)
