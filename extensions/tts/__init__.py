from google.cloud.texttospeech import TextToSpeechAsyncClient
from .listeners import ExtensionTTSListeners
from .commands import ExtensionTTSCommands
from .config import subcategories, options
from discord.ext.commands import Cog
from .logic import ExtensionTTSLogic
from .models import GuildTTS
from client import Client


class ExtensionTTS(
    Cog,
    ExtensionTTSLogic,
    ExtensionTTSListeners,
    ExtensionTTSCommands
):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.tts = TextToSpeechAsyncClient.from_service_account_info(
            self.client.project.google_cloud.model_dump()
        )
        self._guilds: dict[int, GuildTTS] = {}
        self.text_corrections: dict[str, str] = {}


def setup(client: Client) -> None:
    client.permissions.register_permission('tts.ban')
    client.config._subcategories += subcategories
    client.config._options += options
    client.add_cog(ExtensionTTS(client))
