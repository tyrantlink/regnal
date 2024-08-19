from discord.oggparse import OggStream
from discord import AudioSource


class TTSAudio(AudioSource):
    def __init__(
        self,
        source: bytes
    ):
        self._packet_iter = OggStream(source).iter_packets()

    def read(self) -> bytes:
        return next(self._packet_iter, b"")

    def is_opus(self) -> bool:
        return True
