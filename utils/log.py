from discord import ApplicationContext,Message
from traceback import format_exception
from utils.tyrantlib import MakeshiftClass
from datetime import datetime
from inspect import stack
from utils.data import db
from time import time

class log:
	def __init__(self,db:db,DEV_MODE:bool) -> None:
		self.db = db
		self.DEV_MODE = DEV_MODE

	async def _submit(self,type:str,message:str,ctx:ApplicationContext=None,do_print:bool=True,format_print:bool=True,**kwargs) -> None:
		if ctx:
			guild = ctx.guild.id if ctx.guild else None
			channel = ctx.channel.id if ctx.channel else None
			author = ctx.author.id if ctx.author else None
		else: guild,channel,author = None,None,None
		if do_print:
			print(f'[{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}]{" [DEV] " if self.DEV_MODE else " "}[{stack()[1].function.upper()}] {message}' if format_print else message)
		log = {
			'ts':time(),
			'dt':datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
			'dev':self.DEV_MODE,
			'type':type,
			'log':message,
			'guild':guild,
			'channel':channel,
			'author':author,
			'data':kwargs}
		await self.db.logs.new('+0',log)

	async def command(self,ctx:ApplicationContext,**kwargs) -> None:
		await self.db.inf.inc('command_usage',['usage',ctx.command.qualified_name])
		await self.db.stats.inc(2,['stats','commands_used'])
		await self._submit('command',f'{ctx.command.qualified_name} was used by {ctx.author} in {ctx.guild.name if ctx.guild else "DMs"}',ctx,**kwargs)

	async def listener(self,ctx:ApplicationContext|Message,**kwargs) -> None:
		match stack()[1].function:
			case 'listener_dad_bot': source = 'dad bot'
			case 'listener_auto_response': source = 'auto response'
			case _: source = 'unknown listener'
		await self._submit('listener',f'{source} was triggered by {ctx.author} in {ctx.guild.name if ctx.guild else "DMs"}',ctx,**kwargs)

	async def talking_stick(self,ctx:MakeshiftClass,**kwargs) -> None:
		await self._submit('talking stick',f'{ctx.author} got the talking stick in {ctx.guild.name if ctx.guild else "DMs"}',ctx,**kwargs)

	async def info(self,message:str,**kwargs) -> None:
		await self._submit('info',message,**kwargs)

	async def error(self,message:Exception|str) -> None:
		if isinstance(log,Exception):
			if format: message = ''.join(format_exception(message))
			if 'The above exception was the direct cause of the following exception:' in message:
				message = ''.join(message).split('\nThe above exception was the direct cause of the following exception:')[:-1]
		await self._submit(message if isinstance(message,str) else ''.join(message))

	async def debug(self,message:str,**kwargs) -> None:
		await self._submit('info',message,**kwargs)
