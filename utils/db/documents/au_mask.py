
from datetime import timedelta
from beanie import Document
from pydantic import Field


class AutoResponseFileMask(Document):
	class Settings:
		name = 'au_mask'
		use_cache = True
		validate_on_save = True
		use_state_management = True
		cache_expiration_time = timedelta(seconds=5)

	au:str = Field(description='auto response id')