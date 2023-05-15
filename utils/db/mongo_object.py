from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection
from typing import Any

class ReadPathError(Exception):
	"""raised when reading an invalid path"""

class MongoObject:
	def __init__(self,db,collection:Collection,_id:str|int,path:list[str]) -> None:
		self.__db   = db
		self._col   = collection
		self.__id   = _id
		self.__path = path

	async def read(self,a_path:list[str]=None) -> dict|Any:
		"""read value"""
		res:dict = await self._col.find_one({'_id':self.__id})
		path = self.__path+(a_path if a_path is not None else [])
		self.__db.session_stats['db_reads'] += 1
		if path:
			for obj in path[:-1]: res = res.get(obj,{})
			try: res = res.get(path[-1])
			except AttributeError: raise ReadPathError(f'path {path} is invalid')
		return res

	async def write(self,value:Any=None,a_path:list[str]=None) -> bool:
		"""write value"""
		await self._col.update_one({'_id':self.__id},{'$set':{'.'.join(self.__path+(a_path if a_path is not None else [])):value}})
		self.__db.session_stats['db_writes'] += 1
		return True

	async def set(self,value:Any=None,a_path:list[str]=None) -> bool:
		"""write value"""
		return self.write(value,a_path)

	async def unset(self,a_path:list[str]=None) -> bool:
		"""remove the specified field"""
		await self._col.update_one({'_id':self.__id},{'$unset':{'.'.join(self.__path+(a_path if a_path is not None else [])):None}})
		self.__db.session_stats['db_writes'] += 1
		return True

	async def append(self,value:Any=None,a_path:list[str]=None) -> bool:
		"""append value to an array"""
		await self._col.update_one({'_id':self.__id},{'$push':{'.'.join(self.__path+(a_path if a_path is not None else [])):value}})
		self.__db.session_stats['db_writes'] += 1
		return True

	async def remove(self,value:Any=None,a_path:list[str]=None) -> bool:
		"""remove value from an array"""
		await self._col.update_one({'_id':self.__id},{'$pull':{'.'.join(self.__path+(a_path if a_path is not None else [])):value}})
		self.__db.session_stats['db_writes'] += 1
		return True

	async def pop(self,position:int=None,a_path:list[str]=None) -> bool:
		"""pop from an array"""
		if position not in [1,-1]: return False # -1 first last value, 1 removes first
		await self._col.update_one({'_id':self.__id},{'$pop':{'.'.join(self.__path+(a_path if a_path is not None else [])):position*-1}})
		self.__db.session_stats['db_writes'] += 1
		return True

	async def inc(self,value:int|float=1,a_path:list[str]=None) -> bool:
		"""increment a number"""
		await self._col.update_one({'_id':self.__id},{'$inc':{'.'.join(self.__path+(a_path if a_path is not None else [])):value}})
		self.__db.session_stats['db_writes'] += 1
		return True

	async def dec(self,value:int|float=1,a_path:list[str]=None) -> bool:
		"""decrement a number"""
		await self.inc(-value,a_path)

	async def delete(self) -> bool:
		"""delete a document by id"""
		await self._col.delete_one({'_id':self.__id})
		self.__db.session_stats['db_writes'] += 1
		return True

	async def new(self,id:int|str,doc:dict|None=None,update:bool=False) -> tuple[bool,int|None]:
		"""create a new document by duplicating the current doc"""
		if isinstance(id,str):
			if id[0] == '+': id = (await self._col.find_one({},sort=[('_id',-1)])).get('_id')+int(id[1:])
		if doc is None: new = await self._col.find_one({'_id':self.__id})
		else: new = doc
		if new.get('_id',self.__id) == self.__id: new.update({'_id':id})
		try: await self._col.insert_one(new)
		except DuplicateKeyError:
			if not update: return (False,None)
			await self._col.replace_one({'_id':id},new)
		self.__db.session_stats['db_reads'] += 2
		self.__db.session_stats['db_writes'] += 1
		return (True,id)