from discord.commands import SlashCommandGroup,Option as option
from utils.tyrantlib import dev_only,get_line_count
from discord.ext.commands import Cog,slash_command
from discord import Embed,ApplicationContext
from os import system,walk
from client import Client
from asyncio import sleep
from json import dumps

class dev_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	dev = SlashCommandGroup('dev','bot owner commands')

	@dev.command(
		name='menu',
		description='primary dev menu')
	async def slash_dev_menu(self,ctx:ApplicationContext) -> None:
		# extensions
		#		enable
		#		disable
		pass