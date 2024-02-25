from client import ClientLarge,ClientSmall,Client
from utils.update_handler import UpdateHandler
from utils.models import BotType,BotData
from utils.log import Logger,LogLevel
from utils.models import Project
from asyncio import run,gather
from tomllib import loads
from aiofiles import open
from os import walk


async def main() -> None:
	# grab project data
	async with open('project.toml','r') as f:
		base_project = loads(await f.read())
	# initialize logger
	log = Logger(
		url = base_project['parseable']['base_url'],
		logstream = base_project['parseable']['logstream'],
		token = base_project['parseable']['token'],
		log_level = LogLevel(base_project['config']['log_level']))
	await log.logstream_init()

	bots:dict[str,Client] = {}

	extensions = next(walk('extensions'))[1]
	bot_dirs = next(walk('bots'))[1]
	for dir in bot_dirs:
		async with open(f'bots/{dir}/bot.toml','r') as f:
			bot_data = BotData.model_validate(loads(await f.read()))

		if not bot_data.enabled:
			log.info(f'skipping {dir} because it is disabled')
			continue

		proj = base_project.copy()
		proj['bot'] = bot_data
		match bot_data.type:
			case BotType.LARGE: bots.update({dir:ClientLarge(Project.model_validate(proj))})
			case BotType.SMALL: bots.update({dir:ClientSmall(Project.model_validate(proj))})
			case _: raise ValueError(f'invalid bot type {bot_data.type}')
		log.info(f'prepared {dir} for launch')

		for extension in extensions:
			if extension in bot_data.disabled_extensions: continue
			bots[dir].load_extension(f'extensions.{extension}')
		if bot_data.custom_extension:
			bots[dir].load_extension(f'bots.{dir}')

	updater = UpdateHandler(log,bots,base_project,base_project['config']['github_secret'])
	log.info('starting clients')
	await gather(updater.initialize(),*[client.start() for client in bots.values()])

if __name__ == '__main__':
	try: run(main())
	except KeyboardInterrupt: pass