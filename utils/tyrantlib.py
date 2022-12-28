from discord import ApplicationContext
from discord.ext.commands import check
from collections.abc import Mapping
from os.path import isdir
from os import walk
from re import sub

sizes = ['bytes','KBs','MBs','GBs','TBs','PBs','EBs','ZBs','YBs']

def merge_dicts(*dicts:dict) -> dict:
	out = {}
	for d in dicts:
		for k,v in d.items():
			if isinstance(v,Mapping): out[k] = merge_dicts(out.get(k,{}),v)
			else: out[k] = v
	return out

def get_dir_size(dir:str) -> str:
	size = 0
	for path,dirs,files in walk(dir):
		for f in files:
			fp = path.join(path,f)
			size += path.getsize(fp)
	return format_bytes(size)

def format_bytes(byte_count:int) -> str:
	size_type = 0
	while byte_count/1024 > 1:
		byte_count = byte_count/1024
		size_type += 1
	return f'{round(byte_count,3)} {sizes[size_type]}'

def convert_time(seconds:int|float,decimal=15) -> str:
	minutes,seconds = divmod(seconds,60)
	hours,minutes = divmod(minutes,60)
	days,hours = divmod(hours,24)
	days,hours,minutes,res = int(days),int(hours),int(minutes),[]
	if decimal == 0: seconds = int(seconds)
	else: seconds = round(seconds,decimal)
	if days: res.append(f'{days} day{"" if days == 1 else "s"}')
	if hours: res.append(f'{hours} hour{"" if hours == 1 else "s"}')
	if minutes: res.append(f'{minutes} minute{"" if minutes == 1 else "s"}')
	if seconds: res.append(f'{seconds} second{"" if seconds == 1 else "s"}')
	return ', '.join(res)

def dev_only(ctx:ApplicationContext=None) -> bool:
	# IF YOU'RE DEBUGGING THIS IN THE FUTURE REMEMBER THAT THIS HAS TO BE AWAITED
	async def perms(ctx,respond=True) -> bool:
		if ctx.author.id == ctx.bot.owner_id: return True
		if respond: await ctx.response.send_message('you must be the bot developer to run this command.',ephemeral=True)
		return False
	return check(perms) if not ctx else perms(ctx,False)

def get_line_count(input_path:str,excluded_dirs:list=None,excluded_files:list=None) -> int:
	if excluded_dirs is None: excluded_dirs = []
	if excluded_files is None: excluded_files = []
	if isdir(input_path):
		line_count = 0
		for path,dirs,files in walk(input_path):
			dirs[:] = [d for d in dirs if d not in excluded_dirs]
			files[:] = [f for f in files if f not in excluded_files]
			for file in files: line_count += get_line_count('/'.join([path,file]))
		return line_count
	else:
		with open(input_path, 'r') as f: file = f.read()
		file = sub(r'^\s*"""(?:[^"]|"{1,2}(?!"))*"""\s*','',file,flags=8)
		file = sub(r'^\s*#.*','',file, flags=8)
		file = sub(r'^\s*','',file, flags=8)
		file = sub(r'\s*$','',file, flags=8)
		return sum(1 for l in file.splitlines() if l.strip())

def split_list(lst:list,size:int) -> list:
	for i in range(0,len(lst),size):
		yield lst[i:i+size]

class MakeshiftClass:
	def __init__(self,**kwargs) -> None:
		"""attr=value will be set"""
		for k,v in kwargs.items():
			setattr(self,k,v)