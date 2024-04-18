from discord import slash_command,ApplicationContext,Option,Member,Embed,TextChannel,Permissions
from utils.pycord_classes import SubCog
from discord.errors import Forbidden
from discord.abc import GuildChannel
from random import choice,randint
from datetime import timedelta


class CustomBotMariCommands(SubCog):
	@slash_command(
		name='hug-mari',
		description='Just be careful with her wings')
	async def slash_hug_mari(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(
			choice([
				'Thanks for the hug!',
				'Hugs for everyone!',
				f'hey {ctx.author.mention} calm down <:mari_uwu:1230351201627799572>']))

	@slash_command(
		name='kiss-da-goddess',
		description='?????')
	async def slash_kiss_da_goddess(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(
			'Don\'t even think about it <:mari_anger:878178656646725632>'
			if randint(0,250) else
			'...fine, just this once <:mari_uwu:1230351201627799572>'
		)

	@slash_command(
		name='sacrifice',
		description='Don\'t do it',
		options=[
			Option(
				Member,
				name='user',
				description='The offering')])
	async def slash_sacrifice(self,ctx:ApplicationContext,user:Member) -> None:
		if user.id == self.client.user.id:
			await ctx.response.send_message(
				f'W̶h̸a̵t̸ ̷d̵o̵ ̶y̴o̸u̷ ̴t̵h̷i̸n̶k̴ ̷y̵o̶u are do̴i̸n̷g̴?̸ {ctx.author.mention}')
			try:
				await user.timeout_for(
					timedelta(seconds=10),
					reason='tried to sacrifice the goddess')
			except Forbidden:
				pass
			return

		await ctx.response.send_message(
			embed=Embed(
				title='I̷̛̚ ̸̅̇a̶̽͠c̴̊͑c̴̒̑ē̵̓p̶̋t your offering',
				description=f'{ctx.author.mention} has sacrificed {user.mention} in the name of our goddess,',
				color=0x1a1a1b,
				image='https://regn.al/custom_bots/mari/god.png'))

	@slash_command(
		name='say',
		description='"I can talk!"',
		options=[
			Option(
				str,
				name='text',
				description='text',),
			Option(
				GuildChannel,
				name='channel',
				description='channel',
				required=False)],
		default_member_permissions=Permissions(manage_messages=True))
	async def slash_say(self,ctx:ApplicationContext,text:str,channel:TextChannel|None=None) -> None:
		channel = channel or ctx.channel
		if not channel.can_send():
			await ctx.response.send_message(
				'I can\'t send messages there!',
				ephemeral=True)
			return

		await channel.send(text)

		await ctx.response.send_message(
			f'Message sent to {channel.mention}',
			ephemeral=True)
