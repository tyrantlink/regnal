from re import sub,search,IGNORECASE,split,match
from discord.ext.commands import Cog
from discord import Message
from main import client_cls
from os.path import exists


class auto_responses_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client

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

		if guild['config']['auto_responses']: await self.listener_auto_response(message)
		if guild['config']['dad_bot']: await self.listener_dad_bot(message)
	
	def au_check(self,response:str,message:Message) -> str|None:
		match response[0]:
			case 'f': return response if '_'.join(response.split('_')[1:]) == message.content else None
			case 'u': return response if int(response.split('_')[0][1:]) == message.author.id and '_'.join(response.split('_')[1:]) == message.content else None
			case 'c': return response if '_'.join(response.split('_')[1:]) in message.content else None
			case 'r': return response if match('_'.join(response.split('_')[1:]),message.content) is not None else None
			case 'e':
				if response[1:3] == 'cs': return response if '_'.join(response.split('_')[1:]) == message.content else None
				else: return response if '_'.join(response.split('_')[1:]).lower() == message.content.lower() else None
			case 'l':
				for i in self.responses[response]:
					if self.au_check(i,message) is not None: return response
		return None

	async def listener_auto_response(self,message:Message) -> None:
		if exists('tmp/reload_au'): self.responses = await self.client.db.inf.read('auto_responses',['au'])
		out = []
		for response in self.responses:
			if (check:=self.au_check(response,message)) is not None: out.append(check)
			if len(out) > 1: return
		if len(out) == 0: return
		match out[0][0]:
			case 'f': send = f'https://cdn.tyrant.link/reg/nal/auto_responses/{self.responses[out[0]]}'
			case 'l': send = '_'.join(out[0].split('_')[1:])
			case _:   send = self.responses[out[0]]
		await message.channel.send(send)
		await self.client.log.listener(message)

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