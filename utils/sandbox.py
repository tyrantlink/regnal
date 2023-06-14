from RestrictedPython import compile_restricted_exec
from RestrictedPython.Guards import safe_builtins,full_write_guard,guarded_iter_unpack_sequence
from RestrictedPython.Eval import default_guarded_getiter
from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor

safe_builtins.update({
	'__metaclass__': type,
	'__name__': __name__,
	'_getiter_': default_guarded_getiter,
	'_iter_unpack_sequence_': guarded_iter_unpack_sequence,
	'_write_': full_write_guard,
	'_getattr_': getattr,
	'math': __import__('math'),
	'random': __import__('random'),
	'collections': __import__('collections'),
	're': __import__('re'),
	'datetime': __import__('datetime')})

async def safe_exec(script:str,local_variables=None) -> dict:
	bytecode = compile_restricted_exec(script)
	if bytecode.errors:
		raise ValueError(bytecode.errors)
	variables = local_variables or {}
	await get_running_loop().run_in_executor(ThreadPoolExecutor(1),exec,bytecode.code,{'__builtins__': safe_builtins},variables)
	return variables