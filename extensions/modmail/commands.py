from discord import message_command,Message,ApplicationContext,Embed,InputTextStyle,slash_command
from .views import ModMailConfirmationView,ModMailView
from utils.pycord_classes import CustomModal,MasterView
from .subcog import ExtensionModMailSubCog
from discord.ui import InputText


class ExtensionModMailCommands(ExtensionModMailSubCog):
	@message_command(
		name = 'modmail report',
		guild_only = True)
	async def message_modmail_report(self,ctx:ApplicationContext,message:Message) -> None:
		guild_doc = await self.client.db.guild(ctx.guild.id)

		if not guild_doc.config.modmail.enabled:
			await self.client.helpers.send_error(ctx,'modmail is not enabled in this server!')
			return

		if not guild_doc.config.modmail.channel:
			await self.client.helpers.send_error(ctx,'the modmail channel has not been set up in this server!')
			return

		if message.author == ctx.user:
			await self.client.helpers.send_error(ctx,'you can\'t report your own message!')
			return

		modal = CustomModal(
			title = 'report message',
			children = [
				InputText(
					label = 'title',
					style = InputTextStyle.short,
					min_length = 1,
					max_length = 50,
					custom_id = 'title'),
				InputText(
					label = 'issue',
					style = InputTextStyle.long,
					min_length = 1,
					max_length = 4000,
					custom_id = 'issue')])

		await ctx.response.send_modal(modal)
		await modal.wait()

		confirmation_view = ModMailConfirmationView(
			client=self.client,
			message=message,
			reporter=ctx.user,
			title=modal.children[0].value,
			issue=modal.children[1].value,
			allow_anonymous=guild_doc.config.modmail.allow_anonymous)

		await modal.interaction.response.send_message(
			embeds=[confirmation_view.title_embed,*confirmation_view.embeds],
			view=confirmation_view,
			ephemeral=True)

	@slash_command(
		name = 'modmail',
		description = 'modmail inbox and reporting')
	async def slash_modmail(self,ctx:ApplicationContext) -> None:
		if ctx.guild:
			guild_doc = await self.client.db.guild(ctx.guild.id)

			if not guild_doc.config.modmail.enabled:
				await self.client.helpers.send_error(ctx,'modmail is not enabled in this server!')
				return

			if not guild_doc.config.modmail.channel:
				await self.client.helpers.send_error(ctx,'the modmail channel has not been set up in this server!')
				return

		mv = MasterView(self.client,
			await self.client.helpers.embed_color(ctx.guild_id))
		view = mv.create_subview(ModMailView,user=ctx.user,guild=ctx.guild)
		await ctx.response.send_message(embed=view.embed,view=view,ephemeral=True)