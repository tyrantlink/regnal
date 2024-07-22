from dev_utils import new_custom_bot
from asyncio import run


options = '\n'.join(
    f'({i}) {o}'
    for i, o in enumerate([
        'new_custom_bot',
    ])
)


async def main():
    match input(f'{options}\nselect an option: '):
        case '0':
            await new_custom_bot()
        case _:
            print('invalid option')
            return await main()

if __name__ == '__main__':
    run(main())
