from discord import slash_command, Permissions, Option, ApplicationContext, Embed, message_command, Message, InteractionContextType, Member
from .subcog import ExtensionAdminSubCog
from datetime import timedelta
from time import time


class ExtensionAdminCommands(ExtensionAdminSubCog):
    @slash_command(
        name='purge',
        description='bulk delete messages from current channel',
        default_member_permissions=Permissions(manage_messages=True),
        contexts={InteractionContextType.guild},
        options=[
            Option(int, name='amount', description='amount of messages to delete', required=True)])
    async def slash_purge(self, ctx: ApplicationContext, amount: int) -> None:
        purged = await ctx.channel.purge(
            limit=amount,
            reason=f'{ctx.author} used /purge'
        )

        await ctx.response.send_message(embed=Embed(
            title=(
                f'successfully purged {len(purged)} message{"" if len(purged) == 1 else "s"}'),
            color=await self.client.helpers.embed_color(ctx.guild_id)),
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @slash_command(
        name='timeout',
        description='custom timeout down to the second (up to 28 days)',
        default_member_permissions=Permissions(moderate_members=True),
        contexts={InteractionContextType.guild},
        options=[
            Option(Member, name='member',
                   description='member to timeout', required=True),
            Option(int, name='days', description='message to purge until',
                   default=0, max_value=28),
            Option(int, name='hours', description='message to purge until',
                   default=0, max_value=28*24),
            Option(int, name='minutes', description='message to purge until',
                   default=0, max_value=28*24*60),
            Option(int, name='seconds', description='message to purge until',
                   default=0, max_value=28*24*60*60)])
    async def slash_timeout(
        self,
        ctx: ApplicationContext,
        member: Member,
        days: int,
        hours: int,
        minutes: int,
        seconds: int
    ) -> None:
        timeout = timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )

        if timeout.total_seconds() == 0:
            await ctx.response.send_message(embed=Embed(
                title='timeout cannot be zero',
                color=await self.client.helpers.embed_color(ctx.guild_id)),
                ephemeral=await self.client.helpers.ephemeral(ctx)
            )
            return

        if timeout.total_seconds() > 28*24*60*60:
            await ctx.response.send_message(embed=Embed(
                title='timeout cannot exceed 28 days (2419200 seconds)',
                color=await self.client.helpers.embed_color(ctx.guild_id)),
                ephemeral=await self.client.helpers.ephemeral(ctx)
            )
            return

        await member.timeout_for(timeout, reason=f'{ctx.author.name} used /timeout')

        await ctx.response.send_message(embed=Embed(
            title=(
                f'successfully timed out {member.mention} for until <t:{int(time()+timeout.total_seconds())}:f>'),
            color=await self.client.helpers.embed_color(ctx.guild_id)),
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @message_command(
        name='purge until here',
        description='bulk delete messages from current channel until this one',
        contexts={InteractionContextType.guild},
        default_member_permissions=Permissions(manage_messages=True))
    async def message_purge_until_here(self, ctx: ApplicationContext, message: Message) -> None:
        purged = await ctx.channel.purge(
            limit=1000,
            after=message.created_at,
            reason=f'{ctx.author} used `purge until here`'
        )

        await ctx.response.send_message(embed=Embed(
            title=(
                f'successfully purged {len(purged)} message{"" if len(purged) == 1 else "s"}'),
            color=await self.client.helpers.embed_color(ctx.guild_id)),
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )
