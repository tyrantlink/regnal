from discord import Interaction,Embed,SelectOption
from discord.errors import Forbidden
from discord.ui import Select
from client import Client


class role_menu_select(Select):
	def __init__(self,client:Client,options:list[SelectOption],placeholder:str,preview:bool=False) -> None:
		self.client = client
		self.preview = preview
		if options is None: options = range(25)
		super().__init__(placeholder=placeholder,min_values=0,max_values=len(options),options=options,custom_id='test')

	async def callback(self,interaction:Interaction) -> None:
		if self.preview: return
		current_roles = [role.id for role in interaction.user.roles]
		option_data = await self.client.db.role_menu(interaction.message.id).options.read()
		possible_options = [option_data[i]['role'] for i in option_data]
		added_roles,removed_roles = [],[]
		for role in possible_options:
			role = interaction.guild.get_role(role)
			if str(role.id) in self.values and role.id not in current_roles:
				try: await interaction.user.add_roles(role)
				except Forbidden:
					await interaction.response.send_message('a permission error has occurred, contact a moderator.',ephemeral=True)
				added_roles.append(role.mention)
			elif str(role.id) not in self.values and role.id in current_roles:
				try: await interaction.user.remove_roles(role)
				except Forbidden:
					await interaction.response.send_message('a permission error has occurred, contact a moderator.',ephemeral=True)
				removed_roles.append(role.mention)
		res = Embed(title='successfully modified roles',color=await self.client.embed_color(interaction))
		if added_roles: res.add_field(name='added',value='\n'.join(added_roles))
		if removed_roles: res.add_field(name='removed',value='\n'.join(removed_roles))
		if added_roles or removed_roles: await interaction.response.send_message(embed=res,ephemeral=True)
