from discord.ui import Button,button,Item,user_select,Select
from discord import Interaction,Embed,Member
from utils.classes import EmptyView
from client import Client


class dev_banning_view(EmptyView):
	def __init__(self,original_view:EmptyView,user:Member,client:Client,embed:Embed) -> None:
		super().__init__(timeout=0)
		self.original_view = original_view
		self.user          = user
		self.client        = client
		self.embed         = embed
		self.selected_user = None
		self.embed.title   = 'dev banning'
		self.add_items(self.user_select,self.back_button,self.ban_button,self.unban_button)

	async def start(self,**kwargs) -> None: await self.reload()

	async def on_error(self,error:Exception,item:Item,interaction:Interaction) -> None:
		await self.client.on_error(interaction,error)

	async def reload(self) -> None:
		self.embed.description = f'currently banned:\n'+('\n'.join([f'<@{i}>' for i in await self.client.db.inf('/reg/nal').banned_users.read()]) or 'None')

	@user_select(
		custom_id='user_select',row=0,
		placeholder='select a user',min_values=0)
	async def user_select(self,select:Select,interaction:Interaction) -> None:
		self.selected_user = select.values[0] if select.values else None
		await interaction.response.defer(ephemeral=True)

	@button(
		label='<',style=2,row=1,
		custom_id='back_button')
	async def back_button(self,button:Button,interaction:Interaction) -> None:
		await interaction.response.edit_message(embed=self.original_view.embed,view=self.original_view)
		self.stop()

	@button(
		label='ban',style=4,row=1,
		custom_id='ban_button')
	async def ban_button(self,button:Button,interaction:Interaction) -> None:
		if self.selected_user is None:
			await interaction.response.defer(ephemeral=True)
			return
		await self.client.db.inf('/reg/nal').banned_users.append(self.selected_user.id)
		await self.client.log.info(f'{self.user.name} modified dev banning',
			author=self.user.id,
			banned={'id':self.selected_user.id,'name':self.selected_user.name,'discriminator':self.selected_user.discriminator})
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)

	@button(
		label='unban',style=3,row=1,
		custom_id='unban_button')
	async def unban_button(self,button:Button,interaction:Interaction) -> None:
		if self.selected_user is None:
			await interaction.response.defer(ephemeral=True)
			return
		await self.client.db.inf('/reg/nal').banned_users.remove(self.selected_user.id)
		await self.client.log.info(f'{self.user.name} modified dev banning',
			author=self.user.id,
			banned={'id':self.selected_user.id,'name':self.selected_user.name,'discriminator':self.selected_user.discriminator})
		await self.reload()
		await interaction.response.edit_message(embed=self.embed,view=self)