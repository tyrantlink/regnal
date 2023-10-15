from pydantic import BaseModel
from enum import Enum

class BotType(Enum):
	SMALL = 0
	LARGE = 1

class BotData(BaseModel):
	enabled:bool # whether the bot is enabled
	type:BotType # bot type
	logstream:str # parseable logstream
	token:str # bot token
	guilds:list[int] # guilds the bot is limited to (unrestricted if empty)
	disabled_extensions:list[str] # disabled extensions by name

class _ProjectConfig(BaseModel):
	dev_bypass:bool # allows users on dev team to access all commands
	base_guilds:list[int] # additional guilds small bots should join (emote servers, etc)
	git_branch:str # branch to pull from

class _ProjectWebhooks(BaseModel):
	support:str # forum channel for issues and suggestions
	updates:str # announcement channel for updates
	errors:str # text channel for error logging

class _ProjectEnv(BaseModel):
	saucenao_key:str # saucenao api key

class _ProjectMongo(BaseModel):
	uri:str # mongo uri

class _ProjectAPI(BaseModel):
	url:str # api url (crapi)

class _ProjectParseable(BaseModel):
	base_url:str # base url for parseable
	token:str # parseable token

class Project(BaseModel):
	config:_ProjectConfig
	bot:BotData
	webhooks:_ProjectWebhooks
	env:_ProjectEnv
	mongo:_ProjectMongo
	api:_ProjectAPI
	parseable:_ProjectParseable

class LastUpdate(BaseModel):
	commit:str
	commit_full:str
	timestamp:int