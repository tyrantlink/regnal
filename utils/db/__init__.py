from beanie import init_beanie
from .documents import User,Guild,AutoResponse
from motor.motor_asyncio import AsyncIOMotorClient
from .documents.inf import Inf,INFVersion,INFTextCorrection,INFCommandUsage,INFQOTD,INFExcuses,INFInsults,INFEightBall,INFBees,INFSauceNao
from .documents.ext.enums import AutoResponseMethod


class _MongoNew:
	@staticmethod
	def user(id:int,username:str) -> User:
		return User(id=id,username=username)

	@staticmethod
	def guild(id:int,name:str,owner:int) -> Guild:
		return Guild(id=id,name=name,owner=owner)
	
	@staticmethod
	def auto_response(id:int,method:AutoResponseMethod,trigger:str,response:str) -> AutoResponse:
		return AutoResponse(id=id,method=method,trigger=trigger,response=response)

class MongoDatabase:
	def __init__(self,mongo_uri:str) -> None:
		self._client = AsyncIOMotorClient(mongo_uri,serverSelectionTimeoutMS=5000)['regnal']

	async def connect(self) -> None:
		await init_beanie(self._client, document_models=[User,Guild,AutoResponse,INFVersion,INFTextCorrection,INFCommandUsage,INFQOTD,INFExcuses,INFInsults,INFEightBall,INFBees,INFSauceNao])

	@property
	def new(self) -> _MongoNew:
		return _MongoNew

	@property
	def inf(self) -> Inf:
		return Inf

	async def user(self,_id:int|str,use_cache:bool=True) -> User|None:
		"""user documents"""
		return await User.find_one({'_id': _id},ignore_cache=not use_cache)

	async def guild(self,_id:int|str,use_cache:bool=True) -> Guild|None:
		"""guild documents"""
		return await Guild.find_one({'_id': _id},ignore_cache=not use_cache)

	async def auto_response(self,_id:int|str,use_cache:bool=True) -> AutoResponse|None:
		"""auto response documents"""
		return await AutoResponse.find_one({'_id': _id},ignore_cache=not use_cache)