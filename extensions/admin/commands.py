from discord import slash_command, Permissions, Option, ApplicationContext, Embed, message_command, Message
from .subcog import ExtensionAdminSubCog


class ExtensionAdminCommands(ExtensionAdminSubCog):
    @slash_command(
        name='purge',
        description='bulk delete messages from current channel',
        guild_only=True, default_member_permissions=Permissions(manage_messages=True),
        options=[
            Option(int, name='amount', description='amount of messages to delete', required=True)])
    async def slash_purge(self, ctx: ApplicationContext, amount: int) -> None:
        purged = await ctx.channel.purge(
            limit=amount,
            reason=f'{ctx.author} used /purge'
        )

        await ctx.response.send_message(embed=Embed(
            title=f'successfully purged {len(purged)} message{"" if len(purged) == 1 else "s"}',
            color=await self.client.helpers.embed_color(ctx.guild_id)),
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @message_command(
        name='purge until here',
        description='bulk delete messages from current channel until this one',
        guild_only=True, default_member_permissions=Permissions(manage_messages=True))
    async def message_purge_until_here(self, ctx: ApplicationContext, message: Message) -> None:
        purged = await ctx.channel.purge(
            limit=1000,
            after=message.created_at,
            reason=f'{ctx.author} used `purge until here`'
        )

        await ctx.response.send_message(embed=Embed(
            title=f'successfully purged {len(purged)} message{"" if len(purged) == 1 else "s"}',
            color=await self.client.helpers.embed_color(ctx.guild_id)),
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )
