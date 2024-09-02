from motor.motor_asyncio import AsyncIOMotorClient
from asyncio import run
from sys import argv


ENABLED_TYPES = [
    'b',
    # 'c',
    # 'u',
    # 'm',
    # 'p',
    # 's'
]

# ? too tired, making it stupid

with open('project.toml', 'r') as f:
    mongo_uri = (
        f.read()
        .split('[mongo]\nuri = \'')
        [1].split('\'\n')[0]
    )


async def main() -> None:
    try:
        user_id = int(argv[1])
    except ValueError:
        print('invalid user id')
        return

    db = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)['regnal']
    user: dict | None = await db['users'].find_one(
        {'_id': user_id},
        projection=['_id', 'data.auto_responses.found', 'username'])

    if user is None:
        print('user not found')
        return

    user_found = set([
        u for u
        in user['data']['auto_responses']['found']
        if u[0] in ENABLED_TYPES
    ])

    all_auto_responses = {
        au["_id"]: f'{"(NSFW) " if au["data"]["nsfw"] else ""}{au["trigger"]}'
        for au in
        await db['auto_responses'].find(
            {}, projection=['_id', 'trigger', 'type', 'data.nsfw']).to_list(None)
        if all((
            au['_id'][0] in ENABLED_TYPES,
            au['type'] != 3
        ))
    }

    missing = sorted(
        all_auto_responses.keys() - user_found,
        key=lambda au_id: int(au_id[1:])
    )

    if not missing:
        print(f'{user["username"]} has all auto responses')
        return

    print(f'{user["username"]} is missing {len(missing)} auto responses:')

    if not any((
        '--full' in argv,
        '-f' in argv
    )):
        print((
            '\n' if len(missing) < 30 else ','
        ).join(missing))
        return

    print('\n'.join([
        f'{au_id} - {all_auto_responses[au_id]}'
        for au_id in missing
    ]))


if __name__ == '__main__':
    run(main())
