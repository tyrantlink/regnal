from google.cloud.texttospeech import TextToSpeechAsyncClient
from .models import UserTTSProfile, TTSMessage, GuildTTS
from discord import Member, Guild, VoiceChannel
from utils.pycord_classes import SubCog
from .models import TTSMessage
from client import Client


class ExtensionTTSSubCog(SubCog):
    def __init__(self, client: Client) -> None:
        self.client: Client
        self.tts: TextToSpeechAsyncClient
        self._guilds: dict[int, GuildTTS]
        self.text_corrections: dict[str, str]
        self.error_profile: UserTTSProfile
        super().__init__()

    async def get_guild_or_join(
        self, guild: Guild, channel: VoiceChannel) -> GuildTTS: ...

    async def reload_voices(self) -> None: ...
    async def get_user_profile(self, user: Member) -> UserTTSProfile: ...

    async def cache_audio(self, message: TTSMessage) -> None: ...

    async def generate_audio(
        self,
        message: str,
        profile: UserTTSProfile
    ) -> TTSMessage: ...

    async def add_message_to_queue(
        self,
        message: TTSMessage,
        guild: Guild
    ) -> None: ...

    def get_file_type(self, filename: str) -> str: ...

    def get_attachment_name(
        self,
        filename: str,
        full_name: bool = False,
        count: int = 1
    ) -> str: ...

    def process_message(self, message: str) -> str: ...
    def process_text_correction(self, message: str) -> str: ...
    async def create_queue(self, guild_id: int) -> None: ...
    async def process_queue(self, guild: Guild) -> None: ...
    async def join_channel(self, channel: VoiceChannel) -> None: ...
    async def disconnect(self, guild: Guild) -> None: ...
