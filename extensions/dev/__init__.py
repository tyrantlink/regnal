from discord import InputTextStyle,Embed,ApplicationContext,Webhook,File
from discord.ext.commands import Cog,slash_command
from utils.atomic_view import CustomModal
from aiohttp import ClientSession
from discord.ui import InputText
from typing import NamedTuple
from .views import ApiView
from client import Client
from io import StringIO
from json import dumps

class ReportData(NamedTuple):
	modal_title:str
	modal_title_placeholder:str
	modal_description_placeholder:str
	thank_you_message:str
	tag:int

class ExtensionDev(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	async def report(self,ctx:ApplicationContext,data:ReportData) -> None:
		modal = CustomModal(
			title=data.modal_title,
			children=[
				InputText(label='title',
					placeholder=data.modal_title_placeholder,
					style=InputTextStyle.short,required=True),
				InputText(label='description',
					placeholder=data.modal_description_placeholder,
					style=InputTextStyle.long,required=False)
		])
		await ctx.response.send_modal(modal)
		await modal.wait()

		title,description = modal.children[0].value,modal.children[1].value
		embed = Embed(title=title,description=description,color=await self.client.helpers.embed_color(ctx.guild_id))
		embed.set_author(name=ctx.author.name,icon_url=ctx.author.avatar.url)
		async with ClientSession() as session:
			wh = Webhook.from_url(self.client.project.webhooks.support,session=session)
			await wh.send(
				username=self.client.user.name,
				avatar_url=self.client.user.avatar.url,
				embed=embed,thread_name=title if len(title) < 100 else f'{title[:97]}...',
				applied_tags=[])

		await modal.interaction.response.send_message(data.thank_you_message,ephemeral=True)

	@slash_command(
		name='suggest',
		description='suggest a feature!')
	async def slash_suggest(self,ctx:ApplicationContext) -> None:
		await self.report(ctx,ReportData(
			modal_title='suggest a new feature!',
			modal_title_placeholder='feature title',
			modal_description_placeholder='feature description',
			thank_you_message='thank you for your suggestion!',
			tag=self.client.project.webhooks.support_suggestion_tag))

	@slash_command(
		name='issue',
		description='report an issue!')
	async def slash_issue(self,ctx:ApplicationContext) -> None:
		await self.report(ctx,ReportData(
			modal_title='report an issue!',
			modal_title_placeholder='issue title',
			modal_description_placeholder='issue description',
			thank_you_message='thank you for your report!',
			tag=self.client.project.webhooks.support_issue_tag))

	@slash_command(
		name='get_data',
		description='get all the data that is stored about you')
	async def slash_get_data(self,ctx:ApplicationContext) -> None:
		user_data = dumps((await self.client.db.user(ctx.author.id)).model_dump(mode='json'),indent=2)
		if len(user_data)+12 > 2000:
			await ctx.response.send_message(file=File(StringIO(user_data),f'user{ctx.author.id}.json'),ephemeral=True)
			return
		await ctx.response.send_message(f'```json\n{user_data}\n```',ephemeral=True)

	@slash_command(
		name='api',
		description='utilize the api!')
	async def slash_api(self,ctx:ApplicationContext) -> None:
		view = ApiView(self.client,ctx.author)
		await ctx.response.send_message(view=view,embed=view.embed,ephemeral=True)


def setup(client:Client) -> None:
	client.add_cog(ExtensionDev(client))