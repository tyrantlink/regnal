from discord import Embed, User, ApplicationContext, Role, InteractionContextType
from discord.commands import Option, slash_command, user_command
from datetime import timedelta, datetime
from .subcog import ExtensionFunSubCog
from random import choice, randint
from .models import Reminder
from asyncio import sleep
from time import time
from re import sub


class ExtensionFunCommands(ExtensionFunSubCog):
    @slash_command(
        name='generate',
        description='generate a sentence',
        options=[
            Option(
                str,
                name='type',
                description='type',
                choices=['insult', 'excuse'])])
    async def slash_generate_insult(self, ctx: ApplicationContext, type: str) -> None:
        data = await getattr(self.client.db.inf, f'{type}s')()

        match type:
            case 'insult':
                result = ' '.join(
                    [
                        choice(data.adjective),
                        choice(data.noun)
                    ]
                )
            case 'excuse':
                result = ' '.join(
                    [
                        choice(data.intro),
                        choice(data.scapegoat),
                        choice(data.delay)
                    ]
                )
            case _:
                raise ValueError(
                    'invalid /generate type, discord shouldn\'t allow this')

        await ctx.response.send_message(
            result,
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @user_command(name='view profile')
    async def user_profile_user(self, ctx: ApplicationContext, user: User) -> None:
        doc = await self.client.db.user(user.id)

        embed = Embed(
            title=f'{user.name}\'s profile',
            description=f'''
                id: {user.id}
                creation date: <t:{int(user.created_at.timestamp())}:f>
                username: {user.name}
                display name: {user.display_name}
            '''.replace('    ', '').strip(),
            color=await self.client.helpers.embed_color(ctx.guild_id)
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        if doc.config.general.private_profile:
            await ctx.response.send_message(
                embed=embed,
                ephemeral=await self.client.helpers.ephemeral(ctx)
            )
            return

        embed.add_field(
            name='statistics',
            value=f'''
                seen messages: {sum(doc.data.statistics.messages.values()):,}
                tts usage: {doc.data.statistics.tts_usage:,}
                api usage: {doc.data.statistics.api_usage:,}
            '''.replace('    ', '').strip()
        )

        if not doc.data.auto_responses.found:
            await ctx.response.send_message(embed=embed, ephemeral=await self.client.helpers.ephemeral(ctx))
            return

        found_description = []
        user_found = set(doc.data.auto_responses.found)

        if base_found := (
            user_found & (
                base_max := set([b.id for b in self.client.au.au.base])
            )
        ):
            found_description.append(
                f'base: {len(base_found)}/{len(base_max)}'
            )

        if mention_found := (
            user_found & set([m.id for m in self.client.au.au.mention()])
        ):
            found_description.append(f'mention: {len(mention_found)}')

        if personal_found := (
            user_found & (
                personal_max := set([p.id for p in self.client.au.au.personal(user.id)])
            )
        ):
            found_description.append(
                f'personal: {len(personal_found)}/{len(personal_max)}'
            )

        if not ctx.guild:
            await ctx.response.send_message(embed=embed, ephemeral=await self.client.helpers.ephemeral(ctx))
            return

        if unique_found := (
            user_found & (
                unique_max := set([u.id for u in self.client.au.au.unique(ctx.guild.id)])
            )
        ):
            found_description.append(
                f'unique: {len(unique_found)}/{len(unique_max)}'
            )

        if custom_found := (
            user_found & (
                custom_max := set([c.id for c in self.client.au.au.custom(ctx.guild.id)])
            )
        ):
            found_description.append(
                f'custom: {len(custom_found)}/{len(custom_max)}'
            )

        embed.add_field(
            name='auto responses found',
            value='\n'.join(found_description)
        )

        await ctx.response.send_message(embed=embed, ephemeral=await self.client.helpers.ephemeral(ctx))

    @slash_command(
        name='hello',
        description='say hello to /reg/nal?')
    async def slash_hello(self, ctx: ApplicationContext) -> None:
        await ctx.response.send_message(
            f'https://regn.al/{"regnal" if randint(0, 100) else "erglud"}.png',
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @slash_command(
        name='roll',
        description='roll dice with standard roll format',
        options=[
            Option(
                str,
                name='roll',
                description='standard roll format e.g. (2d6+1+2+1d6-2)')])
    async def slash_roll(self, ctx: ApplicationContext, roll: str) -> None:
        rolls, modifiers = [], 0

        embed = Embed(
            title=f'roll: {roll}',
            color=await self.client.helpers.embed_color(ctx.guild_id)
        )

        if (roll := roll.lower()).startswith('d'):
            roll = f'1{roll}'

        roll = sub(r'[^0-9\+\-d]', '', roll).split('+')

        for i in roll:
            if '-' in i and not i.startswith('-'):
                roll.remove(i)
                roll.append(i.split('-')[0])
                for e in i.split('-')[1:]:
                    roll.append(f'-{e}')

        for i in roll:
            e = i.split('d')
            try:
                [int(r) for r in e]
            except:
                await ctx.response.send_message(
                    'invalid input',
                    ephemeral=await self.client.helpers.ephemeral(ctx)
                )
                return
            match len(e):
                case 1:
                    modifiers += int(e[0])
                case 2:
                    if int(e[1]) < 1:
                        await ctx.response.send_message(
                            'invalid input',
                            ephemeral=await self.client.helpers.ephemeral(ctx)
                        )
                        return
                    for _ in range(int(e[0])):
                        res = randint(1, int(e[1]))
                        rolls.append(res)
                case _:
                    await ctx.response.send_message(
                        'invalid input',
                        ephemeral=await self.client.helpers.ephemeral(ctx)
                    )

        if rolls and not len(rolls) > 1024:
            embed.add_field(name='rolls:', value=rolls, inline=False)

        if modifiers != 0:
            embed.add_field(
                name='modifiers:',
                value=f"{'+' if modifiers > 0 else ''}{modifiers}",
                inline=False
            )

        embed.add_field(
            name='result:',
            value='{:,}'.format(sum(rolls)+modifiers)
        )

        await ctx.response.send_message(
            embed=embed,
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @slash_command(
        name='time',
        description='/reg/nal can tell time.')
    async def slash_time(self, ctx: ApplicationContext) -> None:
        await ctx.response.send_message(
            f'<t:{int(time())}:T>',
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @slash_command(
        name='8ball',
        description='ask the 8ball a question',
        options=[
            Option(
                str,
                name='question',
                description='question to ask',
                max_length=512)])
    async def slash_8ball(self, ctx: ApplicationContext, question: str) -> None:
        answer = choice(await self.client.db.inf.eight_ball())

        embed = Embed(
            title=question,
            description=f'**{answer}**',
            color=await self.client.helpers.embed_color(ctx.guild_id)
        )

        embed.set_author(
            name=(
                'magic 8 ball'
                if randint(0, 100) else
                f'{self.client.user.name}\'s eighth ball'
            ),
            icon_url='https://regn.al/8ball.png'
        )

        await ctx.response.send_message(
            embed=embed,
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @slash_command(
        name='color',
        description='generate a random color')
    async def slash_color(self, ctx: ApplicationContext) -> None:
        colors = [randint(0, 255) for _ in range(3)]
        colors_hex = ''.join([hex(c)[2:] for c in colors])

        await ctx.response.send_message(
            embed=Embed(
                title=f'random color: #{colors_hex}',
                description='\n'.join(
                    [f'{l}: {c}' for l, c in zip(['R', 'G', 'B'], colors)]
                ),
                color=int(colors_hex, 16)),
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @slash_command(
        name='random_user',
        description='get random user with role',
        contexts={InteractionContextType.guild},
        options=[
            Option(
                Role,
                name='role',
                description='role to roll users from'),
            Option(
                bool,
                name='ping',
                description='ping the result user? (requires mention_everyone)')])
    async def slash_random(self, ctx: ApplicationContext, role: Role, ping: bool) -> None:
        if ping and not ctx.author.guild_permissions.mention_everyone:
            await ctx.response.send_message('you need the `mention everyone` permission to ping users', ephemeral=True)
            return

        result = choice(role.members)

        await ctx.response.send_message(
            f"{result.mention if ping else result} was chosen!",
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

    @slash_command(
        name='bees',
        description='bees.',
        contexts={InteractionContextType.guild})
    async def slash_bees(self, ctx: ApplicationContext) -> None:
        if ctx.guild.id in self.bees_running:
            await ctx.response.send_message(
                'there may only be one bees at a time.',
                ephemeral=await self.client.helpers.ephemeral(ctx))
            return

        if ctx.channel.name != 'bees':
            await ctx.response.send_message(
                'bees must be run in a channel named `bees`.',
                ephemeral=await self.client.helpers.ephemeral(ctx))
            return

        await ctx.response.send_message(
            'why. you can\'t turn it off. this is going to go on for like, 2 hours, 44 minutes, and 30 seconds. why.',
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )

        self.bees_running.add(ctx.guild.id)
        for line in await self.client.db.inf.bees():
            try:
                await ctx.channel.send(line)
            except Exception:
                pass
            await sleep(5)

        self.bees_running.discard(ctx.guild.id)

    @slash_command(
        name='remind_me',
        description='set a reminder; defaults to 1 hour',
        options=[
            Option(
                str,
                name='message',
                description='what do you want to be reminded of?',
                required=True),
            Option(
                int,
                name='hours',
                description='hours',
                min_value=0,
                max_value=23,
                required=False),
            Option(
                int,
                name='minutes',
                description='minutes',
                min_value=1,
                max_value=59,
                required=False)])
    async def slash_remind_me(self, ctx: ApplicationContext, message: str, hours: int = 0, minutes: int = 0) -> None:
        if hours is None:
            hours = 0

        if minutes is None:
            minutes = 0

        if minutes == 0 and hours == 0:
            hours = 1

        reminder = Reminder(
            user=ctx.author,
            trigger_time=(
                datetime.now() + timedelta(
                    hours=hours,
                    minutes=minutes)
            ).timestamp(),
            reminder=message
        )

        response = f'ok, i\'ll remind you to {message} in'

        if hours:
            response += f' {hours} hour{"s" if hours > 1 else ""}'

        if minutes:
            if hours:
                response += ' and'
            response += f' {minutes} minute{"s" if minutes > 1 else ""}'

        if not ctx.author.can_send():
            response += '\n\nwarning: you have direct messages disabled, so i won\'t be able to remind you'

        self.pending_reminders.add(reminder)

        await ctx.response.send_message(
            response,
            ephemeral=await self.client.helpers.ephemeral(ctx)
        )
