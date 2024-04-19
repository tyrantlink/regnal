from utils.db.documents.ext.flags import APIFlags
from utils.db import MongoDatabase,User
from aiohttp import ClientSession
from base64 import b64decode
from os.path import exists
from tomllib import loads
from pathlib import Path


BASE_BOT_TOML = """enabled = {enabled}
type = {bot_type} # 0 for normal, 1 for sharded
logstream = '{logstream}' # logstream name, must be unique
token = '{discord_token}' # discord bot token
api_token = '{api_token}' # CrAPI token
guilds = {guilds} # restrict to these guilds, or leave empty for unrestricted
disabled_extensions = {disabled_extensions} # extensions to disable by name
custom_extension = {custom_extension} # loads custom extension from __init__.py in the same directory"""

CUSTOM_EXTENSION_FILE = """from client import Client


def setup(client:Client):
	...
	# client.add_cog(...)"""

async def load_db() -> MongoDatabase:
	with open('project.toml','r') as f:
		project = loads(f.read())
	db = MongoDatabase(project['mongo']['uri'])
	await db.connect()
	return db

def get_options() -> tuple[str,str,str,bool]:
	#? this is like, the worse way to do this but i am very tired
	bot_name = None
	while bot_name is None:
		inp = input('bot name (must be unique): ')
		if not inp:
			print('bot name cannot be empty')
			continue
		if exists(f'bots/{inp}'):
			print('bot name already exists')
			continue
		bot_name = inp

	bot_type = None
	while bot_type is None:
		inp = input('bot type (0 for normal, 1 for sharded): ')
		if inp not in ('0','1'):
			print('invalid bot type')
			continue
		bot_type = inp
	
	token = None
	while token is None:
		inp = input('discord bot token: ')
		if not inp:
			print('discord bot token cannot be empty')
			continue
		token = inp
	
	guilds = None
	while guilds is None:
		inp = input('guilds to restrict to (comma separated, no space): ')
		if not inp:
			guilds = []
		else:
			guilds = [int(g) for g in inp.split(',')]
	
	disabled_extensions = None
	while disabled_extensions is None:
		inp = input('disabled extensions (comma separated, no space): ')
		if not inp:
			disabled_extensions = []
		else:
			disabled_extensions = inp.split(',')
	
	custom_extension = None
	while custom_extension is None:
		inp = input('custom extension (y/n): ')
		if inp not in ('y','n'):
			print('invalid custom extension')
			continue
		custom_extension = inp == 'y'
	
	bot_toml = BASE_BOT_TOML.format(
		enabled = 'true',
		bot_type = bot_type,
		logstream = bot_name,
		discord_token = token,
		api_token = 'will be created later',
		guilds = guilds,
		disabled_extensions = disabled_extensions,
		custom_extension = str(custom_extension).lower())

	print(f'\n{bot_toml}\n')
	inp = input('is this correct? (y/n): ').lower()
	if inp != 'y':
		return get_options()
	
	return (
		bot_toml,
		bot_name,
		token,
		custom_extension)

async def create_bot_user(bot_name:str,token:str) -> str:
	dev_token = input('enter dev CrAPI token: ')
	bot_id = int(b64decode(f"{token.split('.')[0]}==").decode())
	print(f'creating bot user ({bot_id})')
	user = User(
		id=bot_id,
		username=f'[bot] {bot_name}')
	user.data.api.permissions = APIFlags.BOT
	await user.save()
	print('created bot user')
	print('creating CrAPI token')
	async with ClientSession(headers={'token':dev_token}) as session:
		async with session.post(f'https://api.regn.al/user/{bot_id}/reset_token') as response:
			match response.status:
				case 200:
					bot_crapi_token = await response.text()
					print('created CrAPI token')
				case _:
					print(f'{response.status} | {await response.text()}')
					return
	return bot_crapi_token

def create_bot_files(bot_name:str,bot_toml:str,custom_extension:bool):
	print('creating bot files')
	Path(f'bots/{bot_name}').mkdir(exist_ok=True)
	with open(f'bots/{bot_name}/bot.toml','w') as f:
		f.write(bot_toml)
	if custom_extension:
		with open(f'bots/{bot_name}/__init__.py','w') as f:
			f.write(CUSTOM_EXTENSION_FILE)
	print('created bot files')


async def main():
	await load_db()
	bot_toml,bot_name,bot_token,custom_extension = get_options()
	bot_crapi_token =  await create_bot_user(bot_name,bot_token)
	if bot_crapi_token is None:
		return
	bot_toml = bot_toml.replace('will be created later',bot_crapi_token)
	create_bot_files(bot_name,bot_toml,custom_extension)
	print('bot successfully created')