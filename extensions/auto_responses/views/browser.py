from utils.tyrantlib import View
from client import Client



class AutoResponseBrowser(View):
	def __init__(self,client:Client) -> None:
		super().__init__()
		self.client = client

