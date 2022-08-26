from datetime import datetime
from os import makedirs,listdir
from os.path import join,isfile
from utils.data import db
from asyncio import wait_for
from traceback import format_exception
from gzip import open as gzopen
from websockets import connect
from discord import ApplicationContext,Message
from utils.tyrantlib import MakeshiftClass
from inspect import stack
from socket import gaierror


class log:
	def __init__(self,db:db,DEV_MODE:bool) -> None:
		self._db = db
		self.DEV_MODE = DEV_MODE

	async def _base(self,log:str,send:bool=True,short_log:str=None,custom:bool=False) -> None:
		if not custom:
			log = f'[{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}]{" [DEV] " if self.DEV_MODE else " "}[{stack()[1].function.upper()}] {log}'
		if short_log is None: short_log = f'[{datetime.now().strftime("%m/%d/%Y %H:%M:%S")}]{" [DEV] " if self.DEV_MODE else " "}[{stack()[1].function.upper()}] {log}'
		with open('log','a') as f:
			f.write(log+'\n' if short_log is None else short_log+'\n')
		with open('log','r') as f:
			txt = f.read()
			if len(txt.encode('utf-8')) > 568870:
				makedirs('logs',exist_ok=True)
				with gzopen(f"logs{len([path for path in listdir('./logs') if isfile(join('.',path))])+1}.gz",'wb') as g:
					g.write(txt.encode('utf-8'))

		print(log)

	async def command(self,ctx:ApplicationContext,log:str=None) -> None:
		await self._db.inf.inc('command_usage',['usage',ctx.command.qualified_name])
		if log is None: log = f'{ctx.command.qualified_name} was used by {ctx.author} in {ctx.guild.name if ctx.guild else "DMs"}'
		await self._base(log,await self._db.inf.read('/reg/nal',['config','command_stdout']))

	async def listener(self,ctx:ApplicationContext|Message,log:str=None) -> None:
		match stack()[1].function:
			case 'listener_dad_bot': source = 'dad bot responded to'
			case 'listener_auto_response': source = 'auto response triggered by'
			case _: source = 'listener triggered by'
		if log is None: log = f'{source} {ctx.author} in {ctx.guild.name if ctx.guild else "DMs"}'
		await self._base(log,await self._db.inf.read('/reg/nal',['config','listener_stdout']))
	
	async def talking_stick(self,ctx:MakeshiftClass,log:str=None) -> None:
		if log is None: log = f'{ctx.author} got the talking stick in {ctx.guild.name if ctx.guild else "DMs"}'
		await self._base(log,await self._db.inf.read('/reg/nal',['config','talking_stick_stdout']))
	
	async def info(self,log:str) -> None:
		await self._base(log,await self._db.inf.read('/reg/nal',['config','info_stdout']))

	async def custom(self,log:str,send:bool=True,short_log:str=None) -> None:
		await self._base(log,send,short_log,custom=True)
	
	async def error(self,log:Exception|str,short_log:str=None) -> None:
		if short_log == None: short_log = str(log)
		if isinstance(log,Exception):
			if format: log = ''.join(format_exception(log))
			if 'The above exception was the direct cause of the following exception:' in log:
				log = ''.join(log).split('\nThe above exception was the direct cause of the following exception:')[:-1]
		await self._base(log if isinstance(log,str) else ''.join(log),short_log=short_log)
	
	async def debug(self,log:str) -> None:
		await self._base(log,await self._db.inf.read('/reg/nal',['config','debug_stdout']))