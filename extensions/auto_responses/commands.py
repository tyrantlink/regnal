from discord import Message, slash_command, ApplicationContext, message_command, InteractionContextType
from .views import AutoResponseBrowserView, AutoResponseInfoView
from .subcog import ExtensionAutoResponsesSubCog


class ExtensionAutoResponsesCommands(ExtensionAutoResponsesSubCog):
    @slash_command(
        name='auto_responses',
        description='browse auto responses you\'ve found',
        contexts={InteractionContextType.guild})
    async def slash_auto_responses(self, ctx: ApplicationContext) -> None:
        view = AutoResponseBrowserView(self.client, ctx.author)

        await view.__ainit__()

        msg = await ctx.response.send_message(embed=view.embed, ephemeral=True)

        # ? i have no clue why i have to do this, but
        await msg.edit(view=view)
        # ? if i don't, then it'll share the view with other users

    @message_command(
        name='au info',
        contexts={InteractionContextType.guild})
    async def message_au_info(self, ctx: ApplicationContext, message: Message) -> None:
        log = await self.client.db.log(message.id)

        if log is None or (au_id := log.data.get('au', None)) is None:
            await ctx.response.send_message(
                'this message is not an auto response!',
                ephemeral=True
            )
            return

        au = self.client.au.get(au_id)

        if au is None:
            await ctx.response.send_message(
                'auto response not found!',
                ephemeral=True
            )
            return

        view = AutoResponseInfoView(self.client, ctx.author, au)

        await view.__ainit__()

        await ctx.response.send_message(embed=view.embed, view=view, ephemeral=True)
