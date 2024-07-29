from utils.pycord_classes import SubCog
from client import Client


class ExtensionFunSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        self.bees_running: set
        self.recent_good_bot_responses: set
        super().__init__()
