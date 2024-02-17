if not 'TYPE_HINT': from client import Client
from discord import Interaction,User,Embed
from utils.pycord_classes import View
from discord.ui import button


class ApiView(View):
	def __init__(self,client:'Client',user:User,**kwargs) -> None:
		super().__init__(**kwargs)
		self.client = client
		self.user = user
		self.embed = Embed(title='api',description='i\'ll put something here eventually, for now it\'s just a token reset portal\nhttps://api.regn.al/docs',color=0x69ff69)
		self.add_item(self.button_reset_token)

	@button(label='reset token',style=4)
	async def button_reset_token(self,_,interaction:Interaction) -> None:
		assert self.user.id == interaction.user.id
		new_token = await self.client.api.reset_user_token(self.user.id)
		embed = Embed(
			title='api token reset!',
			description='WARNING: this is the only time you will be able to see this token, make sure to save it somewhere safe!',
			color=0x69ff69)
		embed.add_field(name='token',value=f'`{new_token}`')
		await interaction.response.send_message(embed=embed,ephemeral=True)

