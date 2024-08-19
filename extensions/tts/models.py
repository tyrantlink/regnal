from google.cloud.texttospeech import VoiceSelectionParams, AudioConfig
from dataclasses import dataclass
from typing import NamedTuple
from hashlib import sha256
from asyncio import Queue
from io import BytesIO


class UserTTSProfile(NamedTuple):
    name: str
    text_correction: bool
    voice: VoiceSelectionParams
    audio_config: AudioConfig


class TTSMessage(NamedTuple):
    profile: UserTTSProfile
    text: str
    data: BytesIO

    def __hash__(self) -> str:
        hash_data = '::'.join(
            [
                self.profile.name,
                self.profile.voice.language_code,
                self.profile.voice.name,
                str(self.profile.audio_config.speaking_rate),
                str(self.profile.text_correction),
                self.text
            ]
        )

        return sha256(hash_data.encode()).hexdigest()


@dataclass
class GuildTTS:
    queue: Queue[TTSMessage]
    last_name: str | None
