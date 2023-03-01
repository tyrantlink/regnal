from utils.classes import CustomModal,ApplicationContext
from discord import InputTextStyle,Embed,ForumChannel
from discord.ext.commands import Cog,slash_command
from utils.tyrantlib import dev_only
from .views.home import home_view
from discord.ui import InputText
from client import Client


class dev_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	async def report(self,ctx:ApplicationContext,mode:str) -> None:
		match mode:
			case 'suggestion':
				title = 'suggest a new feature'
				response = 'thank you for your suggestion'
			case 'issue':
				title = 'report an issue'
				response = 'thank you for reporting this issue'
			case _: raise
		channel = await self.client.db.inf('/reg/nal').config.support.read()
		channel:ForumChannel = self.client.get_channel(channel) or await self.client.fetch_channel(channel)
		modal = CustomModal(None,title,[
			InputText(label='title',placeholder=f'title of {mode}'),
			InputText(label='details',placeholder=f'details of {mode}',style=InputTextStyle.long,required=False)])
		await ctx.response.send_modal(modal)
		await modal.wait()
		embed = Embed(
			title=modal.children[0].value,
			description=modal.children[1].value if len(modal.children) == 2 else None,
			color=await self.client.embed_color(ctx))
		embed.set_author(name=str(ctx.user),url=ctx.user.jump_url,icon_url=ctx.user.avatar.url)
		thread = await channel.create_thread(name=modal.children[0].value,embed=embed,
			applied_tags=[tag for tag in channel.available_tags if tag.name in [mode,'open']])
		await modal.interaction.response.send_message(embed=Embed(
			title=response,
			description=f'[view the thread here](<{thread.jump_url}>)\n[join the development server](<https://discord.gg/4mteVXBDW7>)',
			color=await self.client.embed_color(ctx)),
			ephemeral=True)
		ctx.output.update({'title':modal.children[0].value,'details':modal.children[1].value if len(modal.children) == 2 else None})

	@slash_command(
		name='dev',
		description='primary dev menu')
	@dev_only()
	async def slash_dev(self,ctx:ApplicationContext) -> None:
		embed_color = await self.client.embed_color(ctx)
		view = home_view(
			client=self.client,
			embed_color=embed_color)
		await ctx.response.send_message(embed=view.embed,view=view,ephemeral=True)

	@slash_command(
		name='suggest',
		description='suggest a new feature')
	async def slash_suggest(self,ctx:ApplicationContext) -> None:
		await self.report(ctx,'suggestion')

	@slash_command(
		name='issue',
		description='report an issue')
	async def slash_issue(self,ctx:ApplicationContext) -> None:
		await self.report(ctx,'issue')