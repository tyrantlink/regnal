from discord import ApplicationContext,message_command,Message,File
from .subcog import ExtensionCryptographySubCog
from regnalrb import qr_code
from io import BytesIO


class ExtensionCryptographyCommands(ExtensionCryptographySubCog):
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