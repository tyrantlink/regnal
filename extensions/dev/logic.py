from discord import InputTextStyle,Embed,ApplicationContext,Webhook
from utils.pycord_classes import CustomModal
from .subcog import ExtensionDevSubCog
from aiohttp import ClientSession
from discord.ui import InputText
from .models import ReportData


class ExtensionDevLogic(ExtensionDevSubCog):
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