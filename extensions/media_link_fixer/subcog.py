from utils.pycord_classes import SubCog
from .classes import MediaFixer
from client import Client

class ExtensionMediaLinkFixerSubCog(SubCog):
	def __init__(self) -> None:
		self.client:Client
		super().__init__()
	
	def find_fixes(self,content:str) -> list[MediaFixer]: ...