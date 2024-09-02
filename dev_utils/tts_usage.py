from motor.motor_asyncio import AsyncIOMotorClient
from asyncio import run
from sys import argv

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
        projection=['_id', 'data.statistics.tts_usage', 'username'])

    if user is None:
        print('user not found')
        return

    all_users = await db['users'].find(
        {}, projection=['_id', 'data.statistics.tts_usage', 'username']).to_list(None)

    total_usage = sum(
        user['data']['statistics']['tts_usage']
        for user in all_users
    )

    # get percentage
    user_percentage = user['data']['statistics']['tts_usage'] / \
        total_usage * 100

    print(f'{user["username"]} is {user_percentage:.3f}% of total tts usage')

    print('\ntop ten:')

    # get top ten
    for i, user in enumerate(
        sorted(
            all_users, key=lambda u: u['data']
            ['statistics']['tts_usage'], reverse=True
        )[:10]
    ):
        print(
            f'{i+1}. {user["username"]} - {user["data"]["statistics"]["tts_usage"]} ({user["data"]["statistics"]["tts_usage"]/total_usage*100:.3f}%)')


if __name__ == '__main__':
    run(main())
