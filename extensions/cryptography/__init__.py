from discord import Cog,slash_command,Permissions,Option,ApplicationContext,Embed,message_command,Message,File
from regnalrb import qr_code
from client import Client
from io import BytesIO


class ExtensionCryptography(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
	
	@message_command(
		name='QR Code')
	async def message_qr_code(self,ctx:ApplicationContext,message:Message) -> None:
		if not message.content:
			await ctx.response.send_message('failed to create QR code. no message content.',ephemeral=await self.client.helpers.ephemeral(ctx))
			return

		await ctx.response.send_message(
			file=File(BytesIO(qr_code(message.content)),'regnal_qr.png',
				description=message.content),
			ephemeral=await self.client.helpers.ephemeral(ctx))


def setup(client:Client) -> None:
	client.add_cog(ExtensionCryptography(client))
