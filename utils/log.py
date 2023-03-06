from utils.classes import ApplicationContext,MakeshiftClass
from traceback import format_exception
from utils.db import MongoDatabase
from datetime import datetime
from discord import Message
from inspect import stack
from time import time

class log:
	def __init__(self,db:MongoDatabase,MODE:str) -> None:
		self.db = db
		self.MODE = MODE

	def print(self,message:str,tag:str,format:bool=True):
		print(f'[{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}]{f" [{self.MODE.upper()}] " if self.MODE != "/reg/nal" else " "}[{tag.upper()}] {message}' if format else message)

	async def _submit(self,tag:str,message:str,ctx:ApplicationContext=None,do_print:bool=True,**kwargs) -> None:
		if ctx:
			guild = ctx.guild.id if ctx.guild else None
			channel = ctx.channel.id if ctx.channel else None
			author = ctx.author.id if ctx.author else None
		else:
			guild = kwargs.pop('guild',None)
			channel = kwargs.pop('channel',None)
			author = kwargs.pop('author',None)
		if do_print: self.print(message,tag,kwargs.get('format_print',True))
		await self.db.log(0).new('+1',{
			'ts':time(),
			'dt':datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
			'mode':self.MODE,
			'type':tag,
			'log':message,
			'guild':guild,
			'channel':channel,
			'author':author,
			'data':kwargs})

	async def command(self,ctx:ApplicationContext,**kwargs) -> None:
		await self.db.inf('/reg/nal').inc(1,['command_usage',ctx.command.qualified_name])
		self.db.session_stats['commands_used'] += 1
		await self._submit('command',f'{ctx.command.qualified_name} was used by {ctx.author} in {ctx.guild.name if ctx.guild else "DMs"}',ctx,**kwargs)

	async def listener(self,ctx:ApplicationContext|Message,**kwargs) -> None:
		match stack()[1].function:
			case 'listener_dad_bot': source = 'dad bot'
			case 'listener_auto_response': source = 'auto response'
			case _: source = 'unknown listener'
		await self._submit('listener',f'{source} was triggered by {ctx.author} in {ctx.guild.name if ctx.guild else "DMs"}',ctx,**kwargs)

	async def talking_stick(self,ctx:MakeshiftClass,**kwargs) -> None:
		await self._submit('talking stick',f'{ctx.author} got the talking stick in {ctx.guild.name if ctx.guild else "DMs"}',ctx,**kwargs)

	def log(self,tag:str,message:str,to_db:bool=True,**kwargs) -> None:
		"""to_db returns a coroutine"""
		if to_db: return self._submit(tag,message,**kwargs)
		else    : self.print(message,tag,kwargs.get('format_print',True))

	def info(self,message:str,to_db:bool=True,**kwargs) -> None:
		"""to_db returns a coroutine"""
		return self.log('info',message,to_db,**kwargs)

	async def error(self,message:Exception|str,**kwargs) -> None:
		if isinstance(message,Exception):
			if format: message = ''.join(format_exception(message))
			if 'The above exception was the direct cause of the following exception:' in message:
				message = ''.join(message).split('\nThe above exception was the direct cause of the following exception:')[:-1]
		await self._submit('error',message if isinstance(message,str) else ''.join(message),**kwargs)

	def debug(self,message:str,to_db:bool=True,**kwargs) -> None:
		"""to_db returns a coroutine"""
		return self.log('debug',message,to_db,**kwargs)