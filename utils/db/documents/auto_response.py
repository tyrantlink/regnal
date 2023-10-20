from .ext.enums import AutoResponseMethod,AutoResponseType
from pydantic import BaseModel,Field
from datetime import timedelta
from beanie import Document
from typing import Optional


class AutoResponse(Document):
	class Settings:
		name = 'auto_responses'
		use_cache = True
		validate_on_save = True
		use_state_management = True
		cache_expiration_time = timedelta(seconds=5)

	class AutoResponseData(BaseModel):
		class AutoResponseFollowup(BaseModel):
			delay:float = Field(0,ge=0,description='auto response followup delay in seconds')
			response:str = Field(description='auto response followup response')

		weight:Optional[int] = Field(None,description='auto response weight (for when multiple auto responses are triggered)')
		chance:Optional[int] = Field(None,description='chance to respond (assuming auto response is selected) None for 100%')
		ignore_cooldown:bool = Field(False,description='auto response ignores cooldown\n\nwarning, people can use this to spam')
		custom:bool = Field(False,description='auto response is guild custom')
		regex:bool = Field(False,description='auto response trigger is regex')
		nsfw:bool = Field(False,description='auto response is nsfw')
		case_sensitive:bool = Field(False,description='auto response trigger is case sensitive')
		delete_trigger:bool = Field(False,description='auto response trigger is deleted')
		user:Optional[int] = Field(None,description='auto response users')
		guild:Optional[int] = Field(None,description='auto response guild')
		source:Optional[str] = Field(None,description='auto response source')
		followups:list[AutoResponseFollowup] = Field([],description='auto response followups')

	id:str = Field(description='auto response id')
	method:AutoResponseMethod = Field(description='auto response method')
	trigger:str = Field(description='auto response trigger')
	response:str = Field(description='auto response response')
	type:AutoResponseType = Field(description='auto response type')
	data:AutoResponseData = Field(description='auto response data')