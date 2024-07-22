from utils.pycord_classes import SubCog
from discord import ApplicationContext
from .models import ReportData
from client import Client


class ExtensionDevSubCog(SubCog):
    def __init__(self) -> None:
        self.client: Client
        super().__init__()

    async def report(self, ctx: ApplicationContext,
                     data: ReportData) -> None: ...
