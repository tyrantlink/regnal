
from discord.commands import slash_command,Option as option,message_command
from .views import role_menu_published_view,role_menu_view
from discord import Embed,Role,Message,Permissions
from utils.classes import ApplicationContext
from discord.ext.commands import Cog
from .shared import role_inputs
from client import Client


class role_menu_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	@Cog.listener()
	async def on_ready(self) -> None:
		self.client.add_view(role_menu_published_view(self.client))

	async def open_role_menu(self,ctx:ApplicationContext,message_id:str) -> None:
		if message_id:
			current_data = await self.client.db.role_menu(int(message_id)).read()
			if not current_data:
				await ctx.respond(f'`[{message_id}]` not found in role menu database',ephemeral=True)
				return
			desc = 'you are editing an existing role menu. after you are finished it will be reposted. the original message will be deleted when you are finished.'
		else:
			desc = 'please choose an option.'
			current_data = {'placeholder':'choose some roles','options':{}}
		embed = Embed(title='create a role menu',description=desc,color=await self.client.embed_color(ctx))
		await ctx.response.send_message(embed=embed,view=role_menu_view(
			client=self.client,
			embed=embed,
			current_data=current_data,
			edit=message_id),
			ephemeral=True)

	@slash_command(
		name='role_menu',
		description='create a role menu',
		guild_only=True,default_member_permissions=Permissions(manage_roles=True),
		options=[
			option(str,name='message_id',description='edit existing role menu. menu wil be recreated',required=False,default=None)])
	async def slash_role_menu(self,ctx:ApplicationContext,message_id:str) -> None:
		await self.open_role_menu(ctx,message_id)

	@message_command(
		name='edit role menu',
		guild_only=True,default_member_permissions=Permissions(manage_roles=True))
	async def message_edit_role_menu(self,ctx:ApplicationContext,message:Message) -> None:
		await self.open_role_menu(ctx,message.id)

	@slash_command(
		name='add_role_to_menu',
		description='/role_menu must be used first',
		guild_only=True,default_member_permissions=Permissions(manage_roles=True),
		options=[
			option(Role,name='role',description='role'),
			option(str,name='name',description='role label'),
			option(str,name='description',description='role description',required=False),
			option(str,name='emoji',description='role emoji',required=False)])
	async def slash_add_role_to_menu(self,ctx:ApplicationContext,role:Role,label:str,description:str,emoji:str) -> None:
		if role_inputs.get(ctx.user.id) is None:
			await ctx.response.send_message(f'unable to find role menu, are you on the add role page?',ephemeral=True)
			return
		role_inputs[ctx.user.id]['response'] = {
			'role':role,
			'label':label,
			'description':description,
			'emoji':emoji}
		role_inputs[ctx.user.id]['event'].set()
		await ctx.response.send_message(f'validating role... dismiss this message',ephemeral=True)
