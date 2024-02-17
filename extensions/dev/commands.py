from discord.ext.commands import slash_command
from discord import ApplicationContext,File
from utils.pycord_classes import SubCog
from .models import ReportData
from io import StringIO
from json import dumps



class ExtensionDevCommands(SubCog):
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