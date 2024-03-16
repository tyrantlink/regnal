from google.cloud.texttospeech import VoiceSelectionParams,AudioConfig
from dataclasses import dataclass
from typing import NamedTuple
from asyncio import Queue
from io import BytesIO

class UserTTSProfile(NamedTuple):
	name:str
	text_correction:bool
	voice:VoiceSelectionParams
	audio_config:AudioConfig

class TTSMessage(NamedTuple):
	profile:UserTTSProfile
	text:str
	data:BytesIO

@dataclass
class GuildTTS:
	queue:Queue[TTSMessage]
	last_name:str|None