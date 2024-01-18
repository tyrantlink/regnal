from .ext.enums import TTSVoices,TTSMode
from pydantic import BaseModel,Field
from typing import Optional,Any
from datetime import timedelta
from beanie import Document


class User(Document):
	class Settings:
		name = 'users'
		use_cache = True
		validate_on_save = True
		use_state_management = True
		cache_expiration_time = timedelta(seconds=1)

	class UserConfig(BaseModel):
		class UserConfigGeneral(BaseModel):
			no_track:bool = Field(False,description='disable found au, message counts, command usage logging and api usage logging\n\nsince found au is disabled, you will not be able to use the --au <id> argument')
			private_profile:bool = Field(False,description='make your profile private\n\nif enabled, your profile will only show id, username, display name and creation date')
			talking_stick:bool = Field(True,description='allows you to recieve the talking stick\n\ndisable to remove potential unwanted pings')
			hide_commands:bool = Field(True,description='commands used will only be visible to you\n\neven disabled, some commands with sensitive information will still be hidden')
			auto_responses:bool = Field(True,description='enable/disable auto responses\n\nif guild.auto_responses.mode is set to disabled, this will be ignored')

		class UserConfigTTS(BaseModel):
			mode:TTSMode = Field(TTSMode.only_when_muted,description='when to use tts')
			name:Optional[str] = Field(...,min_length=1,max_length=32,description='name used by tts\n\nif not set, your current display name will be used')
			auto_join:bool = Field(False,description='automatically join voice channel\n\nif disabled, you will have to invite tts manually with {cmd_ref[tts join]}')
			voice:Optional[TTSVoices] = Field(None,description='voice used by tts\n\nif not set, guild.tts.default_voice will be used')
			speaking_rate:float = Field(0.8,ge=0.25,le=4,description='speaking rate used by tts')
			text_correction:bool = Field(True,description='silently corrects text so it\'s more accurately pronounced')
		
		general:UserConfigGeneral = Field(description='general options')
		tts:UserConfigTTS = Field(description='text-to-speech options')

	class UserData(BaseModel):
		class UserDataAPI(BaseModel):
			token:Optional[str] = Field(None,pattern=r'^\$2[ayb]\$.{56}$',description='api token')
			permissions:int = Field(0,description='api permissions')
		
		class UserDataAutoResponses(BaseModel):
			found:list[str] = Field([],description='auto responses found')
			disabled:list[str] = Field([],description='auto responses disabled')
		
		class UserDataStatistics(BaseModel):
			messages:dict[str,int] = Field({},description='message counts by guild id\n\nlegacy data under _legacy')
			api_usage:int = Field(0,description='api calls made')
			tts_usage:int = Field(0,description='tts characters used')

		api:UserDataAPI = Field(description='api data')
		auto_responses:UserDataAutoResponses = Field(description='auto response data')
		statistics:UserDataStatistics = Field(description='user statistics')
		flags:int = Field(0,description='flags the user has')
		extra:dict[str,Any] = Field({},description='extra data')

	id:int = Field(description='user\'s discord id')
	username:str = Field(description='user\'s discord username')
	config:UserConfig = Field(description='user config')
	data:UserData = Field(description='user data')
