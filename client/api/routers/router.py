if not 'TYPE_HINT': from ..crapi import CrAPI

class CrAPIRouter:
	def __init__(self,crapi:'CrAPI') -> None:
		self.crapi = crapi
		self.session = crapi.session