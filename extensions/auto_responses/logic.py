from discord.errors import Forbidden, NotFound, HTTPException
from utils.db.documents.ext.enums import AutoResponseType
from utils.db.documents.ext.enums import AUCooldownMode
from .subcog import ExtensionAutoResponsesSubCog
from asyncio import create_task, sleep
from discord import Message, Thread
from .classes import ArgParser
from time import perf_counter


class ExtensionAutoResponsesLogic(ExtensionAutoResponsesSubCog):
    async def cooldown(self, id: int, time: int) -> None:
        self._cooldowns.add(id)
        await sleep(time)
        self._cooldowns.discard(id)

    async def auto_response_handler(self, message: Message, args: ArgParser) -> None:
        # grab guild and user
        guild = await self.client.db.guild(message.guild.id)
        user = await self.client.db.user(message.author.id)

        # find matching response
        au = await self.client.au.get_response(
            message=message,
            args=args,
            overrides=guild.data.auto_responses.overrides,
            cross_guild=guild.config.auto_responses.allow_cross_guild_responses,
            custom_only=guild.config.auto_responses.custom_only
        )

        if au is None:
            return

        channel = (
            message.channel.parent
            if isinstance(message.channel, Thread)
            else message.channel
        )
        if all((
            not args.force,
            guild.config.auto_responses.cooldown_mode != AUCooldownMode.none,
            not au.data.ignore_cooldown
        )):
            match guild.config.auto_responses.cooldown_mode:
                case AUCooldownMode.user if (
                    message.author.id not in self._cooldowns
                ):
                    pass
                case AUCooldownMode.channel if (
                    channel.id not in self._cooldowns
                ):
                    pass
                case AUCooldownMode.guild if (
                    message.guild.id not in self._cooldowns
                ):
                    pass
                case _:
                    create_task(
                        self.client.helpers.notify_reaction(message, '❄️')
                    )
                    return

        followups = au.data.followups
        embeds = None

        match au.type:
            case AutoResponseType.text:
                response = au.response
            case AutoResponseType.file:
                response = await self.client.api.au.create_masked_url(au.id)
            case AutoResponseType.script:
                st = perf_counter()
                script_response = await self.client.au.execute_au(au, message, args)
                et = perf_counter()

                if script_response is None:
                    return

                response = script_response.content
                embeds = script_response.embeds
                followups = script_response.followups or au.data.followups

            case _:
                return

        reference = (
            message.reference
            if args.reply and args.delete
            else message
            if au.data.reply or args.reply
            else None
        )

        response_message_pending = message.channel.send(
            content=response,
            embeds=embeds,
            reference=reference,
            mention_author=False
        )

        if not args.delete:
            await sleep(args.wait or 0)
            response_message = await response_message_pending

        if args.delete:
            self.client.recently_deleted.add(message.id)
            try:
                await message.delete()
                await sleep(args.wait or 0)
                response_message = await response_message_pending
            except (
                Forbidden,
                NotFound,
                HTTPException
            ) as e:
                self.client.log.error(
                    (
                        f'failed to delete message by {message.author.name} in {message.guild.name}'),
                    guild_id=message.guild.id,
                    metadata={
                        'au_id': au.id,
                        'original_deleted': args.delete,
                        'error': str(e)}
                )

        if not args.delete and au.data.suppress_trigger_embeds:
            try:
                await message.edit(suppress=True)
            except (Forbidden, NotFound):
                pass

        sent_messages = [response_message.id]

        clean_au = self.client.au.get(au.id)
        clean_au.statistics.trigger_count += 1
        await clean_au.save_changes()

        time_taken = (
            f' (execution time: {(et-st)*1000:.2f}ms)'
            if au.type == AutoResponseType.script
            else ''
        )

        self.client.log.info(
            (
                f'auto response {au.id} triggered by {message.author.name} in {message.guild.name}{time_taken}'),
            guild_id=message.guild.id,
            metadata={
                'au_id': au.id,
                'original_deleted': args.delete}
        )

        if not any((args.force, au.data.ignore_cooldown)):
            match guild.config.auto_responses.cooldown_mode:
                case AUCooldownMode.user:
                    cooldown_id = message.author.id
                case AUCooldownMode.channel:
                    cooldown_id = channel.id
                case AUCooldownMode.guild:
                    cooldown_id = message.guild.id
                case _:
                    cooldown_id = None

            create_task(self.cooldown(
                cooldown_id, guild.config.auto_responses.cooldown)
            )

        # add to user found if no arguments were passed and user no track is disabled
        if (
            not args and
            au.id not in user.data.auto_responses.found and
            not user.config.general.no_track
        ):
            user.data.auto_responses.found = list(set(
                user.data.auto_responses.found) | {au.id}
            )

            await user.save_changes()

            create_task(self.client.helpers.notify_reaction(
                message, '⭐', delay=3)
            )
        # send followups
        for followup in followups:
            async with message.channel.typing():
                await sleep(followup.delay)

                msg = await message.channel.send(followup.response)

                sent_messages.append(msg.id)

        for msg_id in sent_messages:
            await self.client.db.new.log(
                id=msg_id,
                data={
                    'au': au.id,
                    'triggerer': message.author.id,
                    'related_messages': sent_messages
                }
            ).save()
