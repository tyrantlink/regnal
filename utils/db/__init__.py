from beanie import init_beanie
from .documents import User,Guild,AutoResponse
from motor.motor_asyncio import AsyncIOMotorClient
from .documents.inf import INFVersion,INFTextCorrection,INFCommandUsage,INFQOTD,INFExcuses,INFInsults,INFEightBall,INFBees,INFSauceNao
from .documents.inf import Inf

class MongoDatabase:
	def __init__(self,mongo_uri:str) -> None:
		self._client = AsyncIOMotorClient(mongo_uri,serverSelectionTimeoutMS=5000)['regnal']

	async def connect(self) -> None:
		await init_beanie(self._client, document_models=[User,Guild,AutoResponse,INFVersion,INFTextCorrection,INFCommandUsage,INFQOTD,INFExcuses,INFInsults,INFEightBall,INFBees,INFSauceNao])

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