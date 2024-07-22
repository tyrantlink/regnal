from utils.pycord_classes import SubCog
from client import Client


class ExtensionModMailSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
