from .classes import MediaFixer
from utils.pycord_classes import SubCog
from client import Client

class ExtensionMediaLinkFixerSubCog(SubCog):
	def __init__(self) -> None:
		self.client:Client
		super().__init__()
		self.embed_cache:dict[int,int]
	
	def find_fixes(self,content:str) -> list[MediaFixer]: ...