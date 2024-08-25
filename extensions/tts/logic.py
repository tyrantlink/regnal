from google.cloud.texttospeech import VoiceSelectionParams, AudioConfig, AudioEncoding, SynthesisInput
from discord import Member, Guild, VoiceClient, VoiceChannel
from .models import UserTTSProfile, TTSMessage, GuildTTS
from .valid_voices import valid_voices
from asyncio import Queue, create_task
from .subcog import ExtensionTTSSubCog
from .tts_audio import TTSAudio
from time import perf_counter
from re import sub, finditer
from random import randint
from io import BytesIO


class ExtensionTTSLogic(ExtensionTTSSubCog):
    async def get_guild_or_join(self, guild: Guild, channel: VoiceChannel) -> GuildTTS | None:
        if (profile := self._guilds.get(guild.id, None)) is None:
            await self.disconnect(guild)
            await self.join_channel(channel)

            profile = self._guilds.get(guild.id, None)

            if profile is None:
                await self.disconnect(guild)
                return None

        return profile

    async def reload_voices(self) -> None:
        self.voices = [  # ? this is super incredibly easy to read god i hate it google why
            voice
            for voice in
            [
                voice.split(':')[-1].replace('"', '')
                for voice in
                [
                    voice.replace(' ', '').split('\n')[2]
                    for voice in str(await self.tts.list_voices()).split('voices ')
                    if voice
                ]
                if ':' in voice
                and voice.startswith('name')
            ]
        ]
        valid_voices.value = set(self.voices)

    async def get_user_profile(self, user: Member) -> UserTTSProfile:
        user_doc = await self.client.db.user(user.id)

        voice = (
            user_doc.config.tts.voice or
            (await self.client.db.guild(user.guild.id)).config.tts.default_voice or
            'en-US-Neural2-H'
        )

        return UserTTSProfile(
            name=user_doc.config.tts.name or user.display_name,
            text_correction=user_doc.config.tts.text_correction,
            voice=VoiceSelectionParams(
                language_code='-'.join(voice.split('-')[:2]),
                name=voice),
            audio_config=AudioConfig(
                audio_encoding=AudioEncoding.OGG_OPUS,
                speaking_rate=user_doc.config.tts.speaking_rate)
        )

    async def cache_audio(self, message: TTSMessage) -> None:
        await self.client.db.new.tts_cache(
            message.__hash__(),
            message.data.getvalue()
        ).save()
        await self.client.db.tts_cache(message.__hash__())

    async def generate_audio(self, message: str, profile: UserTTSProfile) -> TTSMessage:
        st = perf_counter()

        tts_message = TTSMessage(
            profile=profile,
            text=message,
            data=BytesIO()
        )

        from_cache = await self.client.db.tts_cache(tts_message.__hash__())

        if from_cache is not None:
            tts_message.data.write(from_cache.data)
            tts_message.data.seek(0)

            self.client.log.debug(
                f'loaded audio from cache for {profile.name} in {perf_counter()-st:.2f}s'
            )

            return tts_message

        req = await self.tts.synthesize_speech(
            input=SynthesisInput(
                text=message),
            voice=profile.voice,
            audio_config=profile.audio_config
        )

        self.client.log.debug(
            f'generated audio for {profile.name} in {perf_counter()-st:.2f}s'
        )

        tts_message.data.write(req.audio_content)
        tts_message.data.seek(0)

        create_task(self.cache_audio(tts_message))

        return tts_message

    async def add_message_to_queue(self, message: TTSMessage, guild: Guild) -> None:
        if guild.id not in self._guilds:
            raise ValueError(
                f'guild {guild.name} ({guild.id}) does not have a tts queue, please run create_queue'
            )

        self._guilds[guild.id].queue.put_nowait(message)

    def get_attachment_name(self, filename: str, full_name: bool = False) -> str:
        if full_name:
            _filename, extension = filename.replace('_', ' ').rsplit('.', 1)
            return ' dot '.join(  # ? google tts is stupid and only reads the dots half the time
                [
                    _filename,
                    extension.upper()
                ]
            )

        match filename.rsplit('.')[-1]:
            case 'png' | 'jpg' | 'jpeg' | 'webp':
                return 'an image'
            case 'gif':
                return 'a gif'
            case 'mp4' | 'webm' | 'mov' | 'avi' | 'mkv':
                return 'a video'
            case 'mp3' | 'wav' | 'flac' | 'ogg':
                return 'an audio file'
            case 'txt' | 'md':
                return 'a text file'
            case ext:
                return f'a{"n" if ext and ext[0] in {"a","e","i","o","u"} else ""} {ext} file'

    def process_message(self, message: str, guild: Guild) -> str:
        # strip markdown
        message = sub(
            r'(?:\~\~|\_\_\*\*\*|\_\_\*\*|\_\_\*|\_\_|\_|\*\*\*|\*\*|\*)(.*?)(?:\~\~|\*\*\*\_\_|\*\*\_\_|\*\_\_|\_\_|\_|\*\*\*|\*\*|\*)',
            r'\g<1>',
            message
        )
        # pronounce slash commands
        message = sub(
            r'<\/((?:\w|\s)+):\d+>',
            r'slash \g<1> ',
            message
        )
        # pronounce emojis
        message = sub(
            r'<a?:(\w+):\d+>',
            r'\g<1>',
            message
        ).replace('_', ' ')
        # pronounce urls
        pre_sub_message = message
        message = sub(
            r'(?:^|\ )<?https?:\/\/(?:.*\.)?(.*)\.(?:.[^/]+)[^\s]+.>?',
            r'a \g<1> link',
            message
        )
        # easter egg
        if all((
            message != pre_sub_message,
            'a tenor link' in message,
            not randint(0, 100)
        )):
            message = message.replace('a tenor link', 'an elevenor link')
        # strip linked urls
        message = sub(
            r'\[(.*)\]\(.*\)',
            r'\g<1>',
            message
        )
        # replace timestamps
        message = sub(
            r'<t:\d+(:[tTdDfFR])?>',
            'a timestamp',
            message
        )
        # replace users
        for match in finditer(r'<@!?(\d+)>', message):
            user = (
                guild.get_member(int(match.group(1))) or
                self.client.get_user(int(match.group(1)))
            )

            message = message.replace(
                match.group(0),
                f' at {user.display_name if user else "a user"}'
            )
        # replace roles
        for match in finditer(r'<@&(\d+)>', message):
            role = guild.get_role(int(match.group(1)))

            message = message.replace(
                match.group(0),
                f' at {role.name if role else "a role"}'
            )
        # replace channels
        for match in finditer(r'<#(\d+)>', message):
            channel = guild.get_channel(int(match.group(1)))

            message = message.replace(
                match.group(0),
                f'{channel.name if channel else "a channel"}'
            )

        return message

    def process_text_correction(self, message: str) -> str:
        return ' '.join(
            [
                word.replace(
                    punctuation_removed,
                    self.text_corrections.get(
                        punctuation_removed,
                        punctuation_removed))
                for word in message.split(' ')
                if (punctuation_removed := sub(r'\,|\.', '', word))
                is not None
            ]
        )

    async def create_queue(self, guild_id: int) -> None:
        if guild_id not in self._guilds:
            self._guilds[guild_id] = GuildTTS(
                queue=Queue(),
                last_name=None
            )

    async def process_queue(self, guild: Guild) -> None:
        if guild.id not in self._guilds:
            await self.create_queue(guild.id)

        voice_client: VoiceClient = guild.voice_client

        while True:
            try:
                message = await self._guilds[guild.id].queue.get()
            except KeyError:
                break  # disconnected from voice channel

            if not voice_client.is_connected():
                voice_client = await voice_client.channel.connect()
                self.client.log.debug(
                    f'no voice client for {guild.name} ({guild.id}), deleting queue')
                break

            await voice_client.play(
                TTSAudio(
                    source=message.data
                ),
                wait_finish=True
            )

        await self.disconnect(guild)

    async def join_channel(self, channel: VoiceChannel) -> None:
        voice_client: VoiceClient = channel.guild.voice_client

        if voice_client is None:
            await channel.connect()
            await self.create_queue(channel.guild.id)
            create_task(self.process_queue(channel.guild))
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

    async def disconnect(self, guild: Guild) -> None:
        if guild.voice_client is not None:
            await guild.voice_client.disconnect()

        self._guilds.pop(guild.id, None)
