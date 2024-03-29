from discord.ext.commands import Cog,message_command,slash_command
from discord.commands import Option as option
from utils.classes import ApplicationContext
from pyqrcode import create as qr_create
from utils.tyrantlib import dev_banned
from base64 import b64encode,b64decode
from ._shared_vars import algo_list
from discord import File,Message
from client import Client
from io import BytesIO

class cryptography_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	def caesar_cipher(self,encode:bool,input:str,shift:int=7) -> str:
		if encode: return ''.join([c if c == ' ' else chr((ord(c) + shift - 65) % 26 + 65) if c.isupper() else chr((ord(c) + shift - 97) % 26 + 97) for c in input])
		else: return ''.join([c if c == ' ' else chr((ord(c) - shift - 65) % 26 + 65) if c.isupper() else chr((ord(c) - shift - 97) % 26 + 97) for c in input])

	@slash_command(
		name='encode',
		description='encode a message',
		options=[
			option(str,name='message',description='encode input'),
			option(str,name='algorithm',description='algorithm to encode with',choices=algo_list),
			option(str,name='argument',description='argument, refer to /help',required=False)])
	async def slash_encode(self,ctx:ApplicationContext,message:str,algorithm:str,argument:str) -> None:
		match algorithm:
			case 'base64': output = b64encode(message.encode()).decode()
			case 'caesar cipher': output = self.caesar_cipher(True,message,int(argument) if argument else 7)
		await ctx.response.send_message(output,ephemeral=await self.client.hide(ctx))
		ctx.output.update({'output':output})

	@slash_command(
		name='decode',
		description='decode a message',
		options=[
			option(str,name='message',description='decode input'),
			option(str,name='algorithm',description='algorithm to decode with',choices=algo_list),
			option(str,name='argument',description='argument, refer to /help',required=False)])
	async def slash_decode(self,ctx:ApplicationContext,message:str,algorithm:str,argument:str) -> None:
		match algorithm:
			case 'base64': output = b64decode(message)
			case 'caesar cipher': output = self.caesar_cipher(False,message,int(argument) if argument else 7)
		await ctx.response.send_message(output,ephemeral=await self.client.hide(ctx))
		ctx.output.update({'output':output})

	@message_command(
		name='QR Code')
	@dev_banned()
	async def message_qr_code(self,ctx:ApplicationContext,message:Message) -> None:
		if message.content == '':
			await ctx.response.send_message('failed to create QR code. no message content.',ephemeral=await self.client.hide(ctx))
			return

		with BytesIO() as qr_binary:
			try: qr = qr_create(message.content)
			except UnicodeEncodeError:
				await ctx.response.send_message('failed to create QR code. unicode encode error.',ephemeral=await self.client.hide(ctx))
				return

			qr.png(qr_binary,1000 // qr.get_png_size(),quiet_zone=2)
			qr_binary.seek(0)
			await ctx.response.send_message(file=File(qr_binary,'regnal_qr_code.png'),ephemeral=await self.client.hide(ctx))

def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(cryptography_commands(client))