from asyncio import run,gather
from utils.models import Project
from tomllib import loads
from os import walk
from aiofiles import open
from utils.models import BotType,BotData
from client import ClientLarge,ClientSmall



async def main() -> None:
	# grab project data
	async with open('project.toml','r') as f:
		base_project = loads(await f.read())

	bots:list[ClientLarge] = []
	
	bot_dirs = next(walk('bots'))[1]
	for dir in bot_dirs:
		async with open(f'bots/{dir}/bot.toml','r') as f:
			bot_data = BotData.model_validate(loads(await f.read()))

		if not bot_data.enabled:
			print(f'skipping {dir} because it is disabled')
			continue

		proj = base_project.copy()
		proj['bot'] = bot_data
		match bot_data.type:
			case BotType.LARGE: bots.append(ClientLarge(Project.model_validate(proj)))
			case BotType.SMALL: bots.append(ClientSmall(Project.model_validate(proj)))
			case _: raise ValueError(f'invalid bot type {bot_data.type}')
	
	await gather(*[client.start() for client in bots])

if __name__ == '__main__':
	run(main())