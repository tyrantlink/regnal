from re import sub,search,IGNORECASE,split,match
from discord.ext.commands import Cog
from discord import Message
from main import client_cls

class auto_responses_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client
		self.responses = None

	@Cog.listener()
	async def on_connect(self):
		self.responses = await self.client.db.inf.read('auto_responses',['au'])

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if message.guild:
			try: guild = await self.client.db.guilds.read(message.guild.id)
			except: guild = await self.client.db.guilds.read(0)
		else: guild = await self.client.db.guilds.read(0)
		if guild is None: return

		try:
			if (
				message.author.bot or
				message.author.id in guild['softbans'] or 
				message.author == self.client.user or 
				await self.client.db.users.read(message.author.id,['config','ignored'])):
					return
		except: return

		if message.guild is None:
			await message.channel.send('https://cdn.tyrant.link/reg/nal/dm.png')
			return

		if self.responses is None:
			self.responses = await self.client.db.inf.read('auto_responses',['au'])

		if guild['config']['auto_responses']:
			if await self.listener_auto_response(message): return
		if guild['config']['dad_bot']: await self.listener_dad_bot(message)
	
	def au_check(self,message:Message) -> tuple[str,str]|None:
		for i in self.responses['contains']:
			if i in message.content.lower(): return ('contains',i)
		if message.content.lower() in self.responses['exact']:
			return ('exact',message.content.lower())
		if message.content in self.responses['exact-cs']:
			return ('exact-cs',message.content)
	
	def get_au(self,category,message) -> dict:
		return self.responses[category][message]

	async def listener_auto_response(self,message:Message) -> None:
		check = self.au_check(message)
		if check is None: return

		data = self.get_au(check[0],check[1])
		if redir:=data.get('redir',False):
			data = self.get_au(check[0],redir)
		
		if (response:=data.get('response',None)) is None: return
		if (user:=data.get('user',None)) is not None and message.author.id is not user: return
		if data.get('file',False): response = f'https://cdn.tyrant.link/reg/nal/auto_responses/{response}'

		await message.channel.send(response)
		await self.client.log.listener(message)
		return True

	async def listener_dad_bot(self,message:Message) -> None:
		response = ''
		input = sub(r'<(@!|@|@&)\d{10,25}>|@everyone|@here','[REDACTED]',sub(r'\*|\_|\~|\`|\|','',message.content))
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