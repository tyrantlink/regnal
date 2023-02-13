from .collections import INF,Guild,Log,Message,Poll,RoleMenu,StatusLog,User
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDatabase:
	def __init__(self,mongo_uri:str) -> None:
		self._client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)['reg-nal']
		self.session_stats = {
			'db_reads': 0,
			'db_writes': 0,
			'messages_seen': 0,
			'commands_used': 0}

	def inf(self,_id:str) -> INF:
		"""infrequently read documents"""
		return INF(self,self._client.INF,_id)

	def guild(self,_id:int) -> Guild:
		"""guild documents"""
		return Guild(self,self._client.guilds,_id)

	def log(self,_id:int) -> Log:
		"""logging documents"""
		return Log(self,self._client.logs,_id)

	def message(self,_id:int) -> Message:
		"""message documents"""
		return Message(self,self._client.messages,_id)

	def poll(self,_id:int) -> Poll:
		"""poll documents"""
		return Poll(self,self._client.polls,_id)

	def role_menu(self,_id:int) -> RoleMenu:
		"""role menu documents"""
		return RoleMenu(self,self._client.role_menu,_id)

	def status_log(self,_id:int|str) -> StatusLog:
		"""status documents"""
		return StatusLog(self,self._client.status_logs,_id)

	def user(self,_id:int|str) -> User:
		"""user documents"""
		return User(self,self._client.users,_id)
