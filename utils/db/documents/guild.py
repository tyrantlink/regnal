from .ext.enums import TWBFMode,AUCooldownMode,TTSVoices
from pydantic import BaseModel,Field
from typing import Optional,Any
from datetime import timedelta
from beanie import Document


class Guild(Document):
	class Settings:
		name = 'guilds'
		use_cache = True
		validate_on_save = True
		use_state_management = True
		cache_expiration_time = timedelta(seconds=1)

	class GuildConfig(BaseModel):
		class GuildConfigGeneral(BaseModel):
			hide_commands:TWBFMode = Field(TWBFMode.disabled,description='commands will only be visible to the user\n\neven disabled, some commands with sensitive information will still be hidden\n\ntrue: commands will always be hidden\nwhitelist: commands will be hidden in selected channels\nblacklist: commands will be hidden in all channels except selected channels\nfalse: commands will never be force hidden')
			embed_color:str = Field('69ff69',min_length=6,max_length=6,pattern=r'^[a-fA-F\d]{6}$',description='color used by embeds\n\nif not set, the default color will be used')
			event_time:str = Field('09:00',min_length=5,max_length=5,pattern=r'^[0-2]\d:[0-5]\d$',description='time used by event command\n\nif not set, the default time will be used')

		class GuildConfigAutoResponses(BaseModel):
			mode:TWBFMode = Field(TWBFMode.enabled,description='enable/disable auto responses\n\ntrue: auto responses enabled in all channels\nwhitelist: auto responses enabled in selected channels\nblacklist: auto responses disabled in selected channels\nfalse: auto responses disabled in all channels')
			cooldown:int = Field(0,ge=0,description='cooldown between auto responses in seconds')
			cooldown_mode:AUCooldownMode = Field(AUCooldownMode.channel,description='cooldown mode\n\nnone: no cooldown\nuser: cooldown per user\nchannel: cooldown per channel\nguild: cooldown server-wide')
			allow_cross_guild_responses:bool = Field(False,description='allow custom auto responses from other guilds to be used (using the --au argument)\n\nvery, very dangerous permission, allows users to send arbitrary auto responses\nuse at your own risk.')

		class GuildConfigLogging(BaseModel):
			enabled:bool = Field(False,description='enable/disable logging\n\nif disabled, all logging will be disabled\nif enabled you can view logs on https://logs.regn.al')
			channel:Optional[int] = Field(None,description='channel used for some logging\nfull logs still visible on https://logs.regn.al')
			log_bots:bool = Field(False,description='enable/disable logging of bot messages')
			log_commands:bool = Field(False,description='enable/disable logging of command usage')
			deleted_messages:bool = Field(False,description='enable/disable logging of deleted messages')
			edited_messages:bool = Field(False,description='enable/disable logging of edited messages')
			member_join:bool = Field(False,description='enable/disable logging of member joins')
			member_leave:bool = Field(False,description='enable/disable logging of member leaves')
			member_ban:bool = Field(False,description='enable/disable logging of member bans')
			member_unban:bool = Field(False,description='enable/disable logging of member unbans')

		class GuildConfigQOTD(BaseModel):
			enabled:bool = Field(False,description='enable/disable qotd\n\nif disabled, all qotd will be disabled')
			channel:Optional[int] = Field(None,description='channel used for qotd\n\nquestions will be sent here at `{self.general.event_time}` (event time)')

		class GuildConfigTTS(BaseModel):
			enabled:bool = Field(True,description='allow tts to be used')
			channels:list[int] = Field([],description='channels where tts is allowed\n\nvoice-text channels will always allow tts')
			default_voice:Optional[TTSVoices] = Field(None,description='default voice used by tts\n\nif not set, the default voice (en-US-Neural2-H) will be used')

		class GuildConfigTalkingStick(BaseModel):
			enabled:bool = Field(False,description='daily random roll to give an active user a specific role\n\nmeant to give users send_messages permissions in a channel, but can be used for anything')
			channel:Optional[int] = Field(None,description='channel used to announce the talking stick')
			role:Optional[int] = Field(None,description='role given to the user')
			limit:Optional[int] = Field(None,description='role that limits who can get the talking stick\n\nif not set, all users can get the talking stick')

		class GuildConfigSauceNao(BaseModel):
			api_key:Optional[str] = Field(None,description='sauce nao api key\n\nif not set, the default api key will be used (with a very low limit)]\n\nget an api key at https://saucenao.com/user.php?page=account-upgrades')

		general:GuildConfigGeneral = Field(description='general options')
		auto_responses:GuildConfigAutoResponses = Field(description='auto response options')
		logging:GuildConfigLogging = Field(description='logging options')
		qotd:GuildConfigQOTD = Field(description='qotd options')
		tts:GuildConfigTTS = Field(description='text-to-speech options')
		talking_stick:GuildConfigTalkingStick = Field(description='talking stick options')
		saucenao:GuildConfigSauceNao = Field(description='sauce nao options')

	class GuildData(BaseModel):
		class GuildDataQOTD(BaseModel):
			class GuildDataQOTDQuestion(BaseModel):
				question:str = Field(min_length=1,max_length=200,description='question to be asked')
				author:str = Field(min_length=1,max_length=32,description='author of the question')
				icon:str = Field(min_length=1,max_length=200,description='icon of the author')

			last_question:int = Field(0,ge=0,description='timestamp of last question sent')
			nextup:list[GuildDataQOTDQuestion] = Field([],description='questions that will be sent next')
			pool:list[GuildDataQOTDQuestion] = Field([],description='questions added to custom pool')
			asked:str = Field('',description='question asked stored as a bitstring')
			asked_custom:str = Field('',description='custom question asked stored as a bitstring')

		class GuildDataTalkingStick(BaseModel):
			current:Optional[int] = Field(None,description='user currently holding the talking stick')

		class GuildDataAutoResponses(BaseModel):
			whitelist:list[int] = Field([],description='channels where auto responses are whitelisted')
			blacklist:list[int] = Field([],description='channels where auto responses are blacklisted')
			disabled:list[str] = Field([],description='auto responses disabled')
			overrides:dict[str,dict] = Field({},description='auto response overrides')

		class GuildDataHideCommands(BaseModel):
			whitelist:list[int] = Field([],description='channels where commands are whitelisted')
			blacklist:list[int] = Field([],description='channels where commands are blacklisted')

		class GuildDataTTS(BaseModel):
			banned:list[int] = Field([],description='users banned from using tts')

		class GuildDataStatistics(BaseModel):
			messages:int = Field(0,ge=0,description='total messages sent')
			commands:int = Field(0,ge=0,description='total commands used')
			questions:int = Field(0,ge=0,description='total questions asked')
			tts:int = Field(0,ge=0,description='total tts characters used')

		activity:dict[str,dict[str,int]] = Field({},max_length=30,description='activity data for at most last 30 days\n\nformat {day:{user_id:count}}')
		qotd:GuildDataQOTD = Field(description='qotd data')
		talking_stick:GuildDataTalkingStick = Field(description='talking stick data')
		auto_responses:GuildDataAutoResponses = Field(description='auto response data')
		hide_commands:GuildDataHideCommands = Field(description='hide commands data')
		tts:GuildDataTTS = Field(description='text-to-speech data')
		statistics:GuildDataStatistics = Field(description='guild statistics')
		flags:int = Field(0,description='flags the guild has')
		extra:dict[str,Any] = Field({},description='extra data')

	id:int = Field(description='guild\'s discord id')
	name:str = Field(description='guild\'s discord name')
	owner:int|None = Field(description='guild\'s discord owner id')
	config:GuildConfig = Field(description='guild config')
	data:GuildData = Field(description='guild data')