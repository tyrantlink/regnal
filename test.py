# from re import fullmatch

# check = r'ma{3,}x'
# tests = [
# 	'max',
# 	'maaaaaaaax',
# 	'maasdfx',
# 	'maaax asdfasdf'
# ]
# for i in tests:
# 	print(fullmatch(check,i))
from utils.data import db as _db
from asyncio import run



async def main():
	db = _db()
	await db.logs.new('+1',{'test':"""this is a multiline string
	wow
	i can't believe it
	this is poggers indeed
	my mates
	crack
	anywhatzit
	imma bounce
	bounce on your
	boy's dick
	ha gottem
	*dabs out*"""})
	print('poggers')
run(main())