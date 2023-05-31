from discord import Message,Thread,Reaction,User
from regex import sub,split,finditer,search,IGNORECASE
from discord.errors import Forbidden,HTTPException
from utils.classes import MixedUser,ArgParser
from asyncio import sleep,create_task
from discord.ext.commands import Cog
from urllib.parse import quote
from random import choices
from client import Client
from time import time
from re import split


class auto_response_listeners(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.cooldowns = {'au':{},'db':{}}
		self.timeouts = []
		self.recent_responses:list[tuple[int,int,list[int]]] = []

	async def timeout(self,message_id:int) -> None:
		self.timeouts.append(message_id)
		await sleep(5)
		try: self.timeouts.remove(message_id)
		except ValueError: pass

	async def recent_response(self,response_data:tuple[int,int,list[int]]) -> None:
		self.recent_responses.append(response_data)
		await sleep(900)
		try: self.recent_responses.remove(response_data)
		except ValueError: pass

	@Cog.listener()
	async def on_reaction_add(self,reaction:Reaction,user:User) -> None:
		if (reaction.message.author.id != self.client.user.id or
				reaction.emoji != '❌'): return
		for response_data in filter(lambda r: r[0] == user.id and (r[1] == reaction.message.id or reaction.message.id in r[2]),self.recent_responses):
			for message_id in (response_data[1],*response_data[2]):
				message = self.client.get_message(message_id)
				if message is None: continue
				try: await message.delete()
				except (Forbidden,HTTPException): pass

	@Cog.listener()
	async def on_message(self,message:Message,user:MixedUser=None) -> None:
		if message is None or message.author.id == self.client.user.id: return
		# ignore webhooks except pk
		if message.webhook_id is not None and user is None: return
		create_task(self.timeout(message.id))

		if message.guild:
			try: guild = await self.client.db.guild(message.guild.id).read()
			except: guild = await self.client.db.guild(0).read()
		else: guild = await self.client.db.guild(0).read()
		if guild is None: return

		if guild.get('config',{}).get('general',{}).get('pluralkit',False) and user is None:
			if (pk:=await self.client.pk.get_message(message.id)):
				if pk is not None and pk.original == message.id:
					await self.on_message(self.client.get_message(pk.id),MixedUser('pluralkit',message.author,
						id=pk.member.uuid,
						bot=False))
					return
		if user is None: user = message.author

		try:
			if (user.bot or
				await self.client.db.user(user.id).config.general.ignored.read() or
				user.id in await self.client.db.inf('/reg/nal').banned_users.read()):
					return
		except: return

		if message.content is None: return
		if message.guild is None:
			await message.channel.send('https://regn.al/dm.png')
			return

		channel = message.channel.parent if isinstance(message.channel,Thread) else message.channel
		if time()-self.cooldowns['au'].get(message.author.id if guild['config']['auto_responses']['cooldown_per_user'] else message.channel.id,0) > guild['config']['auto_responses']['cooldown']:
			match guild['config']['auto_responses']['enabled']:
				case 'enabled':
					if await self.listener_auto_response(message,user): return
				case 'whitelist' if channel.id in guild['data']['auto_responses']['whitelist']:
					if await self.listener_auto_response(message,user): return
				case 'blacklist' if channel.id not in guild['data']['auto_responses']['blacklist']:
					if await self.listener_auto_response(message,user): return
				case 'disabled': pass
		if time()-self.cooldowns['db'].get(message.author.id if guild['config']['auto_responses']['cooldown_per_user'] else message.channel.id,0) > guild['config']['dad_bot']['cooldown']:
			match guild['config']['dad_bot']['enabled']:
				case 'enabled':
					if await self.listener_dad_bot(message,user): return
				case 'whitelist' if channel.id in guild['data']['dad_bot']['whitelist']:
					if await self.listener_dad_bot(message,user): return
				case 'blacklist' if channel.id not in guild['data']['dad_bot']['blacklist']:
					if await self.listener_dad_bot(message,user): return
				case 'disabled': pass

	async def listener_auto_response(self,message:Message,user:MixedUser) -> None:
		args = ArgParser()
		content = args.parse(message.content)
		user_found = await self.client.db.user(user.id).data.au.read()
		args.force = args.force and user.id in self.client.owner_ids
		for au in (self.client.au.get((args.au if args.au is not None and (args.force or any((search(fr'{args.au}:\d+',s) for s in user_found))) else None)),
							self.client.au.match(content,{'custom':True,'guild':str(message.guild.id)}),
							self.client.au.match(content,{'custom':False,'guild':str(message.guild.id)}),
							self.client.au.match(content,{'custom':False,'guild':None})):
			if au is None: continue

			if au._id in await self.client.db.guild(message.guild.id).data.auto_responses.disabled.read(): continue
			weights,responses = zip(*[(w,r) for w,r in [(None,au.response)]+au.alt_responses])
			if args.alt is not None:
				try: responses[args.alt]
				except IndexError: args.alt = None
				else: args.alt = args.alt if args.force or (au.guild and not au.custom) or f'{au._id}:{args.alt}' in user_found else None
			response_index = args.alt if args.alt is not None else choices([i for i in range(len(responses))],[w or (100-sum(filter(None,weights)))/weights.count(None) for w in weights])[0]
			response = responses[response_index]
			if response is None: continue
			if (au.nsfw and not message.channel.nsfw) and not args.force: continue
			if au.user is not None and (str(message.author.id) != au.user and not args.force): continue
			if au.file:
				if message.attachments: continue
				response = (f'https://regn.al/gau/{au.guild}/' if au.guild else 'https://regn.al/au/')+quote(response)
			if au.regex and (match:=search(au.trigger,message.content,IGNORECASE)) is not None:
				groups = {f'g{i}':'' for i in range(1,11)}
				groups.update({f'g{k}':'character limit' if len(v) > 100 else v for k,v in enumerate(match.groups()[:10],1) if v is not None})
				try: response = response.format(**groups)
				except KeyError as e: response = f'invalid group {e.args[0][1:]}\ngroup must be between 1 and 10'

			if message.id not in self.timeouts: continue
			try: response_data = (message.author.id,(await message.channel.send(response)).id,[])
			except (Forbidden,HTTPException): continue
			if args.delete and (au.file or args.force):
				try: await message.delete(reason='auto response deletion')
				except Forbidden: pass
				else: await self.client.log.info(f'auto response trigger deleted by {message.author}')
			for delay,followup in au.followups:
				async with message.channel.typing():
					await sleep(delay)
				response_data[2].append((await message.channel.send(followup)).id)
			create_task(self.recent_response(response_data))

			if not au.custom and au.guild is None:
				response_id = f'{au._id}:{response_index}'
				if response_id not in user_found and not await self.client.db.user(user.id).config.general.no_track.read():
					await self.client.db.user(user.id).data.au.append(response_id)

			self.cooldowns['au'].update({user.id if await self.client.db.guild(message.guild.id).config.auto_responses.cooldown_per_user.read() else message.channel.id:int(time())})
			await self.client.log.listener(message,id=au._id,category=au.method,trigger=au.trigger,response=response,original_deleted=args.delete)
			return True
		else: return False

	def rand_name(self,message:Message,splitter:str) -> str:
		options,weights = [message.guild.me.display_name if message.guild else self.client.user.name],[]
		if splitter in ["i'm"]:
			options += ['proud of you','not mad, just disappointed']
			weights += [0.005,0.01]
		weights.insert(0,1-sum(weights))
		return choices(options,weights)[0]

	async def listener_dad_bot(self,message:Message,user:MixedUser) -> None:
		response,splitter = '',''
		input = sub(r"""<(@!|@|@&)\d{10,25}>|@everyone|@here|(https?:\/\/[^\s]+.)""",'[REDACTED]',sub(r'\*|\_|\~|\`|\|','',message.content))
		splitters = "i'm|im|i am|i will be|i've|ive"
		for s in finditer(splitters,input,IGNORECASE):
			if (s is None or
				(s.span()[0] != 0 and input[s.span()[0]-1] != ' ') or
				(s.span()[1] < len(input) and input[s.span()[1]] != ' ')): continue
			response,splitter = ''.join(split(s.captures()[0],input,1,IGNORECASE)[1:]),s.captures()[0].lower()

		if response == '': return
		name = self.rand_name(message,splitter)

		if message.id not in self.timeouts: return False
		nl = '\n'
		out_message = f'hi{split(f"[,.;{nl}]",response)[0]}, {splitter} {name}'
		if len(out_message) > 2000: out_message = f'hi{response.split(".")[0][:1936]} (character limit), {splitter} {name}'
		try: response_data = (message.author.id,(await message.channel.send(out_message)).id,[])
		except Forbidden: return False

		create_task(self.recent_response(response_data))
		self.cooldowns['db'].update({user.id if await self.client.db.guild(message.guild.id).config.dad_bot.cooldown_per_user.read() else message.channel.id:int(time())})
		await self.client.log.listener(message,splitter=splitter,name=name)


def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(auto_response_listeners(client))