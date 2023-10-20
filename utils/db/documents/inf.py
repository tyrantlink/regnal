from pydantic import BaseModel,Field
from beanie import Document

class INFBase(Document):
	class Settings:
		name = 'inf'
		validate_on_save = True
		use_state_management = True
	id:str

class INFVersion(INFBase):
	value:str = Field(description='version number x.x.x')

class INFTextCorrection(INFBase):
	value:dict[str,str] = Field(description='dictionary of text corrections')

class INFCommandUsage(INFBase):
	value:dict[str,int] = Field(description='dictionary of command usage')

class INFQOTD(INFBase):
	value:list[str] = Field(description='list of qotd questions')

class INFExcuses(INFBase):
	class INFExcuseObject(BaseModel):
		intro:list[str] = Field(description='list of excuse intros')
		scapegoat:list[str] = Field(description='list of scapegoats')
		delays:list[str] = Field(description='list of delays')

	value:INFExcuseObject = Field(description='excuse object')

class INFInsults(INFBase):
	class INFInsultObject(BaseModel):
		adjective:list[str] = Field(description='list of adjectives')
		noun:list[str] = Field(description='list of nouns')

	value:INFInsultObject = Field(description='insult object')

class INFEightBall(INFBase):
	value:list[str] = Field(description='list of eight ball responses')

class INFBees(INFBase):
	value:list[str] = Field(description='list of bees :wink:')

class INFSauceNao(INFBase):
	value:str = Field(description='sauce nao api key')

class Inf:
	@staticmethod
	async def version() -> INFVersion:
		"""inf version"""
		return await INFVersion.find_one({'_id': 'version'})

	@staticmethod
	async def text_correction() -> INFTextCorrection:
		"""inf text correction"""
		return await INFTextCorrection.find_one({'_id': 'text_correction'})

	@staticmethod
	async def command_usage() -> INFCommandUsage:
		"""inf command usage"""
		return await INFCommandUsage.find_one({'_id': 'command_usage'})

	@staticmethod
	async def qotd() -> INFQOTD:
		"""inf qotd"""
		return await INFQOTD.find_one({'_id': 'qotd'})

	@staticmethod
	async def excuses() -> INFExcuses:
		"""inf excuses"""
		return await INFExcuses.find_one({'_id': 'excuses'})

	@staticmethod
	async def insults() -> INFInsults:
		"""inf insults"""
		return await INFInsults.find_one({'_id': 'insults'})

	@staticmethod
	async def eight_ball() -> INFEightBall:
		"""inf eight ball"""
		return await INFEightBall.find_one({'_id': 'eight_ball'})

	@staticmethod
	async def bees() -> INFBees:
		"""inf bees"""
		return await INFBees.find_one({'_id': 'bees'})

	@staticmethod
	async def saucenao() -> INFSauceNao:
		"""inf saucenao"""
		return await INFSauceNao.find_one({'_id': 'saucenao'})