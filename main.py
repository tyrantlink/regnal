from asyncio import run, gather, set_event_loop_policy
from client import ClientLarge, ClientSmall, Client
from utils.update_handler import UpdateHandler
from utils.models import BotType, BotData
from utils.log import Logger, LogLevel
from uvloop import EventLoopPolicy
from utils.models import Project
from os.path import exists
from aiofiles import open
from tomllib import loads
from os import walk

set_event_loop_policy(EventLoopPolicy())

try:
    from regnalrb import is_compiled as regnalrb_is_compiled
    assert regnalrb_is_compiled()
except (ImportError, AssertionError):
    print('ERROR: the /reg/nal rust bindings have not been compiled\nplease run `maturin develop -rm regnalrb/Cargo.toml`')
    exit()


async def main() -> None:
    if not exists('project.toml'):
        print('ERROR: project.toml not found, please copy it from project.toml.example and fill it out!')
        exit()

    async with open('project.toml', 'r') as f:
        base_project = loads(await f.read())

    auto_logstream_padding: list = (
        [base_project['parseable']['logstream']]
        if base_project['parseable']['logstream_padding'] == -1
        else []
    )

    log = Logger(
        url=base_project['parseable']['base_url'],
        logstream=base_project['parseable']['logstream'],
        logstream_padding=base_project['parseable']['logstream_padding'],
        token=base_project['parseable']['token'],
        log_level=LogLevel(base_project['config']['log_level'])
    )

    await log.logstream_init()

    bots: dict[str, Client] = {}

    extensions = next(walk('extensions'))[1]

    if base_project['developer']['dev_mode']:
        extensions = list(
            set(extensions) &
            set(base_project['developer']['dev_extensions'])
        )

    bot_dirs = next(walk('bots'))[1]
    bot_data_array: dict[str, BotData] = {}

    for dir in bot_dirs:
        if not exists(f'bots/{dir}/bot.toml'):
            log.error(f'bot.toml not found in bots/{dir}')
            continue

        async with open(f'bots/{dir}/bot.toml', 'r') as f:
            bot_data = BotData.model_validate(loads(await f.read()))

        bot_data_array.update({dir: bot_data})

        if auto_logstream_padding and bot_data.enabled:
            auto_logstream_padding.append(bot_data.logstream)

    if auto_logstream_padding:
        log.logstream_padding = max([len(s) for s in auto_logstream_padding])

    for dir, bot_data in bot_data_array.items():
        if not bot_data.enabled:
            log.info(f'skipping {dir} because it is disabled')
            continue

        proj = base_project.copy()
        proj['bot'] = bot_data

        match bot_data.type:
            case BotType.LARGE: bots[dir] = ClientLarge(Project.model_validate(proj))
            case BotType.SMALL: bots[dir] = ClientSmall(Project.model_validate(proj))
            case _: raise ValueError(f'invalid bot type {bot_data.type}')

        bots[dir].log.logstream_padding = log.logstream_padding

        # ? have to load as extension because python ownership bullshit
        bots[dir].load_extension('client.commands')

        bots[dir].enabled_extensions = {
            extension for extension in extensions
            if extension not in bot_data.disabled_extensions
        }

        for extension in bots[dir].enabled_extensions.copy():
            bots[dir].load_extension(f'extensions.{extension}')

        if bot_data.custom_extension:
            bots[dir].load_extension(f'bots.{dir}')

        log.info(f'prepared {dir} for launch')

    updater = UpdateHandler(
        log,
        bots,
        base_project,
        base_project['config']['github_secret']
    )

    log.info('starting clients')

    await gather(
        updater.initialize(),
        *[client.start() for client in bots.values()]
    )

if __name__ == '__main__':
    try:
        run(main())
    except KeyboardInterrupt:
        pass
