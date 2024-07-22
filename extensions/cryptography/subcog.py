from utils.pycord_classes import SubCog
from client import Client


class ExtensionCryptographySubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        super().__init__()
