from pytz import timezone,UnknownTimeZoneError
if not 'TYPE_HINT': from client import Client
from .errors import ConfigValidationError
from .models import ConfigOption
from discord import User,Member

async def user_general_no_track(client:'Client',option:ConfigOption,value:bool,user:User|Member) -> tuple[bool,str|None]:
	if not value: return value,None
	user_doc = await client.db.user(user.id)
	user_doc.data.statistics.messages = {}
	user_doc.data.statistics.commands = {}
	user_doc.data.statistics.tts_usage = 0
	user_doc.data.auto_responses.found = []
	await user_doc.save_changes()
	return value,None

async def guild_general_timezone(client:'Client',option:ConfigOption,value:str,user:User|Member) -> tuple[str,str|None]:
	try: zone = timezone(value)
	except UnknownTimeZoneError: raise ConfigValidationError(f'unknown timezone `{value}`')
	return zone.zone,None

async def guild_general_embed_color(client:'Client',option:ConfigOption,value:str,user:User|Member) -> tuple[str,str|None]:
	if value.startswith('#'): value = value[1:]
	return value,None