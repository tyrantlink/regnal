
# ? it's not real imma deal with it later

# from RestrictedPython.Guards import safe_builtins,full_write_guard,guarded_iter_unpack_sequence
# from RestrictedPython.Eval import default_guarded_getiter,default_guarded_getitem
# from RestrictedPython import compile_restricted_exec
# from concurrent.futures import ThreadPoolExecutor
# from asyncio import get_running_loop

# class RestrictedMessage:
# 	class _channel:
# 		def __init__(self,id,name) -> None:
# 			self.id = id
# 			self.name = name

# 	class _guild:
# 		def __init__(self,id,name) -> None:
# 			self.id = id
# 			self.name = name

# 	class _user:
# 		def __init__(self,id,name,display_name) -> None:
# 			self.id = id
# 			self.name = name
# 			self.display_name = display_name

# 	def __init__(self,**kwargs):
# 		self.id = kwargs.get('message_id',None)
# 		self.channel = self._channel(
# 			kwargs.get('channel_id',None),
# 			kwargs.get('channel_name',None))
# 		self.guild = self._guild(
# 			kwargs.get('guild_id',None),
# 			kwargs.get('guild_name',None))
# 		self.author = self._user(
# 			kwargs.get('author_id',None),
# 			kwargs.get('author_name',None),
# 			kwargs.get('author_display_name',None))
# 		self.timestamp = kwargs.get('timestamp',None)
# 		self.content = kwargs.get('content',None)

# allowed_imports = [
# 	'math',
# 	'collections',
# 	're',
# 	'random',
# 	'time',
# 	'datetime']

# def attempted_import(name,*args,**kwargs):
# 	if name in allowed_imports: return __import__(name,*args,**kwargs)
# 	raise KeyError(f'imports are not allowed! failed to import "{name}" ')

# safe_builtins.update({
# 	'__metaclass__': type,
# 	'__name__': __name__,
# 	'_getiter_': default_guarded_getiter,
# 	'_getitem_': default_guarded_getitem,
# 	'_iter_unpack_sequence_': guarded_iter_unpack_sequence,
# 	'_write_': full_write_guard,
# 	'__import__': attempted_import,
# 	'math': __import__('math'),
# 	'random': __import__('random'),
# 	'collections': __import__('collections'),
# 	're': __import__('re'),
# 	'time': __import__('time'),
# 	'datetime': __import__('datetime')})

# async def safe_exec(script:str,local_variables=None) -> dict:
# 	bytecode = compile_restricted_exec(script)
# 	if bytecode.errors:
# 		raise ValueError(bytecode.errors)
# 	variables = local_variables or {}
# 	await get_running_loop().run_in_executor(ThreadPoolExecutor(1),exec,bytecode.code,{'__builtins__': safe_builtins},variables)
# 	return variables
