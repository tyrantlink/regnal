from pymongo.errors import DuplicateKeyError
import motor.motor_asyncio,collections.abc
from pymongo.collection import Collection
from typing import Any
from time import time

with open('mongo') as mongo:
	client = motor.motor_asyncio.AsyncIOMotorClient(mongo.read().replace('\n',''), serverSelectionTimeoutMS=5000)['reg-nal']

class env:
	def __init__(self,env_dict:dict) -> None:
		self.token:str = None
		self.dev_token:str = None
		self.shlink:str = None
		self.mongo_pub:str = None
		self.mongo_prv:str = None
		self.config:dict = None
		self.activities:dict = None
		self.help:dict = None
		self.statcord_key:str = None
		self.saucenao_key:str = None
		for k,v in env_dict.items():
			setattr(self,k,v)

class utils():
	def merge(dict:dict,new:dict) -> dict:
		for key,value in new.items():
			if isinstance(value, collections.abc.Mapping): dict[key] = utils.merge(dict.get(key,{}),value)
			else: dict[key] = value
		return dict

	def form_path(path:list,value:Any,dotnotation:bool=False) -> dict:
		res = current = {}
		length = len(path)
		if len(path) == 1: return {path[0]:value}
		if dotnotation: return {f"{'.'.join(path)}":value}
		for index,name in enumerate(path):
			if index+1 == length:
				current[name] = value
				current = current[name]
			else:
				current[name] = {}
				current = current[name]
		return res

class DataCollection():
	def __init__(self,collection:Collection) -> None:
		self.collection = collection
		self.stats = client.status_logs

	@property
	def raw(self) -> Collection:
		"""returns raw pymongo Collection"""
		return self.collection

	async def read(self,id:int|str,path:list=[]) -> Any:
		"""returns the value given at the specified path"""
		res = await self.collection.find_one({'_id':id})
		for key in path: res = res[key]
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_reads'],1,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],2,True)})
		return res

	async def write(self,id:int|str,path:list=[],value:Any=None) -> bool:
		"""write the given object to the given path"""
		await self.collection.replace_one({'_id':id},utils.merge((await self.collection.find_one({'_id':id})),utils.form_path(path,value)))
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_reads'],1,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],3,True)})
		return True
	
	async def append(self,id:int|str,path:list=[],value:Any=None) -> bool:
		"""append the specified element to an array"""
		await self.collection.update_one({'_id':id},{'$push':utils.form_path(path,value,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],2,True)})
		return True

	async def remove(self,id:int|str,path:list=[],value:Any=None) -> bool:
		"""remove the specified element from an array"""
		await self.collection.update_one({'_id':id},{'$pull':utils.form_path(path,value,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],2,True)})
		return True
	
	async def unset(self,id:int|str,path:list=[],value:Any=None) -> bool:
		"""delete the specified field"""
		await self.collection.update_one({'_id':id},{'$unset':utils.form_path(path,value,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],2,True)})
		return True
	
	async def pop(self,id:int|str,path:list=[],position:int=None) -> bool:
		"""removes the first or last element of an array\nthe element is not returned"""
		if position not in [1,-1]: return False # -1 first last value, 1 removes first
		await self.collection.update_one({'_id':id},{'$pop':utils.form_path(path,position*-1,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],2,True)})
		return True

	async def inc(self,id:int|str,path:list=[],value:int|float=1) -> bool:
		"""increment a number"""
		await self.collection.update_one({'_id':id},{'$inc':utils.form_path(path,value,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],2,True)})
		return True
	
	async def dec(self,id:int|str,path:list=[],value:int|float=1) -> bool:
		"""decrement a number"""
		await self.inc(id,path,-value)

	async def delete(self,id:int|str) -> bool:
		"""delete a document by id"""
		await self.collection.delete_one({'_id':id})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],2,True)})
		return True

	async def new(self,id:int|str,input=None) -> bool:
		if isinstance(id,str):
			if id[0] == '+': id = await self.raw.count_documents({})+int(id[1:])
		if input == None:
			res = await self.collection.find_one({'_id':0})
			res.update({'_id':id})
		else:
			res = input
			try: res['_id']
			except KeyError: res['_id'] = id
		try: await self.collection.insert_one(res)
		except DuplicateKeyError: return False
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_reads'],1,True)})
		await self.stats.update_one({'_id':2},{'$inc':utils.form_path(['stats','db_writes'],3,True)})
		return True

class db:
	async def ready(self) -> None:
		doc_count = await self.stats.raw.count_documents({})
		if doc_count >= 2:
			for doc in range(2,doc_count):
				await self.stats.inc(1,['stats','db_reads'],await self.stats.read(doc,['stats','db_reads']))
				await self.stats.inc(1,['stats','db_writes'],await self.stats.read(doc,['stats','db_writes']))
				await self.stats.inc(1,['stats','messages_seen'],await self.stats.read(doc,['stats','messages_seen']))
				await self.stats.inc(1,['stats','commands_used'],await self.stats.read(doc,['stats','commands_used']))
				await self.stats.delete(doc)
		await self.stats.new(2)
		await self.stats.write(2,['timestamp'],time())

	@property
	def inf(self) -> DataCollection: return DataCollection(client.INF)
	@property
	def dd_roles(self) -> DataCollection: return DataCollection(client.dd_roles)
	@property
	def guilds(self) -> DataCollection: return DataCollection(client.guilds)
	@property
	def logs(self) -> DataCollection: return DataCollection(client.logs)
	@property
	def messages(self) -> DataCollection: return DataCollection(client.messages)
	@property
	def polls(self) -> DataCollection: return DataCollection(client.polls)
	@property
	def stats(self) -> DataCollection: return DataCollection(client.status_logs)
	@property
	def test(self) -> DataCollection: return DataCollection(client.test)
	@property
	def users(self) -> DataCollection: return DataCollection(client.users)