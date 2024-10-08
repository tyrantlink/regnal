from google.cloud.texttospeech import VoiceSelectionParams, AudioConfig, AudioEncoding
from google.api_core.exceptions import ServiceUnavailable, InternalServerError
from utils.db.documents.ext.flags import UserFlags
from utils.db.documents.ext.enums import TTSMode
from discord import Message, Member, VoiceState
from .subcog import ExtensionTTSSubCog
from discord.ext.commands import Cog
from .models import UserTTSProfile
from asyncio import create_task
from re import fullmatch


class ExtensionTTSListeners(ExtensionTTSSubCog):
    @Cog.listener()
    async def on_connect(self) -> None:
        self.text_corrections = await self.client.db.inf.text_correction()
        await self.reload_voices()

        self.error_profile = UserTTSProfile(
            name=self.client.user.display_name,
            text_correction=False,
            voice=VoiceSelectionParams(
                language_code='en-US',
                name='en-US-Neural2-H'),
            audio_config=AudioConfig(
                audio_encoding=AudioEncoding.OGG_OPUS,
                speaking_rate=0.8)
        )

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if (
            message.guild is None or
            message.author.bot or
            message.webhook_id or
            message.content.startswith('-') or
            message.author.voice is None
        ):
            return

        # ignore empty messages
        if all((
            not message.content,
            not message.attachments,
            not message.stickers
        )):
            return

        user_doc = await self.client.db.user(message.author.id)
        guild_doc = await self.client.db.guild(message.guild.id)
        # ignore if not in voice channel or a tts channel
        if not message.channel.id in [
            message.author.voice.channel.id,
            *guild_doc.config.tts.channels
        ]:
            return
        # check user voice state
        if message.author.voice.deaf or message.author.voice.self_deaf:
            return

        match user_doc.config.tts.mode:
            case TTSMode.never:
                return
            case TTSMode.only_when_muted if (
                not message.author.voice.self_mute and
                not message.content.startswith('+')
            ):
                return
            case TTSMode.always | _:
                pass
        # join channel if user has auto join, and client is not in a voice channel
        if self._guilds.get(message.guild.id, None) is None:
            if not user_doc.config.tts.auto_join:
                return

            await self.join_channel(message.author.voice.channel)
        # ensure that the client is in the correct channel
        if (
            message.guild.voice_client is None or
            message.guild.voice_client.channel.id != message.author.voice.channel.id
        ):
            return

        text = message.content

        if text:
            if (
                user_doc.config.tts.mode == TTSMode.only_when_muted and
                not message.author.voice.self_mute and
                message.content.startswith('+')
            ):
                text = text.removeprefix('+')

            text = self.process_message(text, message.guild)

            if user_doc.config.tts.text_correction:
                text = self.process_text_correction(text)

        attachment_types = {}
        checked_types = set()
        if not user_doc.config.tts.read_filenames:
            for attachment in message.attachments:
                file_type = self.get_file_type(attachment.filename)
                attachment_types[
                    file_type
                ] = attachment_types.get(file_type, 0) + 1

        for attachment in message.attachments:
            file_type = self.get_file_type(attachment.filename)
            if (
                not user_doc.config.tts.read_filenames and
                file_type in checked_types
            ):
                continue

            checked_types.add(file_type)
            name = self.get_attachment_name(
                attachment.filename,
                user_doc.config.tts.read_filenames,
                attachment_types.get(file_type, 0)
            )
            text += (
                f' along with {name}'
                if text else
                name
            )

        for sticker in message.stickers:
            name = sticker.name.replace('_', ' ')
            text += (
                f' along with {name}'
                if text else
                name
            )

        if user_doc.config.tts.text_correction:
            await self.client.db.inf.text_correction()

        profile = await self.get_user_profile(message.author)
        guild_data = await self.get_guild_or_join(message.guild, message.author.voice.channel)

        if guild_data is None:
            return

        if guild_data.last_name != profile.name:
            phrase = (
                'said:'
                if (
                    message.content and
                    not fullmatch(
                        r'(?:^|\ )<?https?:\/\/(?:.*\.)?(.*)\.(?:.[^/]+)[^\s]+.>?',
                        message.content
                    )
                ) else
                'sent'
            )
            text = f'{profile.name} {phrase} {text}'
            self._guilds[message.guild.id].last_name = profile.name

        # ensure message word length
        if not (word_lengths := {len(w) for w in text.split()}):
            return
        # validate message length
        if (
            not user_doc.data.flags & UserFlags.UNLIMITED_TTS and
            len(text) > 800 or
            max(word_lengths) > 64
        ):
            create_task(self.client.helpers.notify_reaction(message))
            return
        # generate audio
        try:
            audio = await self.generate_audio(text, profile)
        except (ServiceUnavailable, InternalServerError):
            audio = await self.generate_audio(
                message='google text to speech is down, please try again later',
                profile=self.error_profile
            )
        # add message to queue
        await self.add_message_to_queue(audio, message.guild)
        # update statistics
        user_doc.data.statistics.tts_usage += len(text)
        guild_doc.data.statistics.tts += len(text)

        await user_doc.save_changes()
        await guild_doc.save_changes()

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member.id == self.client.user.id and after.channel is None:
            await self.disconnect(member.guild)
            return

        if member.guild.id not in self._guilds:
            return

        if (
            before.channel is not None and
            {self.client.user.id} == set(before.channel.voice_states.keys())
        ):
            await self.disconnect(member.guild)
            return
