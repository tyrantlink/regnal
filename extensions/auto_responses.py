from re import sub,search,IGNORECASE,split
from discord.ext.commands import Cog
from discord import File,Message
from main import client_cls
from os import getcwd




class auto_responses_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if message.guild:
			try: guild = await self.client.db.guilds.read(message.guild.id)
			except: guild = await self.client.db.guilds.read(0)
		else: guild = await self.client.db.guilds.read(0)
		if guild == None: return

		try:
			if (
				message.author.bot or
				message.author.id in guild['softbans'] or 
				message.author == self.client.user or 
				await self.client.db.users.read(message.author.id,['config','ignored'])):
					return
		except: return

		if guild['config']['auto_responses']: await self.listener_auto_response(message)
		if guild['config']['dad_bot']: await self.listener_dad_bot(message)
	
	async def listener_auto_response(self,message:Message) -> None:
		responses = await self.client.db.inf.read('auto_responses')
		user,file,owner = responses['user'],responses['file'],responses['owner']
		if message.author.id == self.client.owner_id and message.content in owner: await message.channel.send(owner[message.content])
		elif message.content in user: await message.channel.send(user[message.content])
		elif message.content in file: await message.channel.send(file=File(f'{getcwd()}/images/memes/{file[message.content]}'))
		else: return
		await self.client.log.listener(message)

	async def listener_dad_bot(self,message:Message) -> None:
		response = ''
		input = sub(r'<(@!|@|@&)\d{18}>|@everyone|@here','[REDACTED]',sub(r'\*|\_|\~|\`|\|','',message.content))
		for p_splitter in ["I'm",'im','I am','I will be']:
			s = search(p_splitter,input,IGNORECASE)

			if s == None: continue
			if s.span()[0] != 0:
				if input[s.span()[0]-1] != ' ': continue
			if input[s.span()[0]+(len(p_splitter))] != ' ': continue

			p_response = split(p_splitter,input,1,IGNORECASE)[1:]
			if len(response) < len(''.join(p_response)): response,splitter = ''.join(p_response),p_splitter

		if response == '': return

		try: await message.channel.send(f'hi{response}, {splitter} {message.guild.me.display_name if message.guild else self.client.user.name}')
		except: await message.channel.send(f'hi{response[:1936]} (character limit), {splitter} {message.guild.me.display_name if message.guild else self.client.user.name}')
		await self.client.log.listener(message)


def setup(client:client_cls) -> None: client.add_cog(auto_responses_cog(client))