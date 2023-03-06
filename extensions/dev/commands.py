from discord import InputTextStyle,Embed,ForumChannel,Webhook
from utils.classes import CustomModal,ApplicationContext
from discord.ext.commands import Cog,slash_command
from aiohttp import ClientSession
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
		modal = CustomModal(None,title,[
			InputText(label='title',placeholder=f'title of {mode}',max_length=100),
			InputText(label='details',placeholder=f'details of {mode}',style=InputTextStyle.long,required=False)])
		await ctx.response.send_modal(modal)
		await modal.wait()
		async with ClientSession() as session:
			message = await Webhook.from_url(f'https://discord.com/api/webhooks/{await self.client.db.inf("/reg/nal").config.support_wh.read()}',session=session
			).send(wait=True,username=ctx.author.name,avatar_url=ctx.author.avatar.url,thread_name=modal.children[0].value,embed=Embed(
				title=modal.children[0].value,
				description=modal.children[1].value if len(modal.children) == 2 else None,
				color=await self.client.embed_color(ctx)))
		await modal.interaction.response.send_message(embed=Embed(
			title=response,
			description=f'[view the thread here](<{message.jump_url}>)\n[join the development server](<https://discord.gg/4mteVXBDW7>)',
			color=await self.client.embed_color(ctx)),
			ephemeral=True)
		ctx.output.update({'title':modal.children[0].value,'details':modal.children[1].value if len(modal.children) == 2 else None})

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