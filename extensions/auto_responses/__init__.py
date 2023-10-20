from utils.db.documents.ext.enums import AutoResponseType,TWBFMode,AUCooldownMode
from discord.errors import Forbidden,NotFound,HTTPException
from utils.db.documents.ext.flags import UserFlags
from .classes import AutoResponses,ArgParser
from discord import Cog,Message,Thread
from asyncio import create_task,sleep
from urllib.parse import quote
from client import Client


class ExtensionAutoResponses(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.client.au = AutoResponses(client)
		self._cooldowns = set()

	async def cooldown(self,id:int,time:int) -> None:
		self._cooldowns.add(id)
		await sleep(time)
		self._cooldowns.remove(id)

	@Cog.listener()
	async def on_connect(self) -> None:
		await self.client.au.reload_au()

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if not message.guild: # ignore dms
			await message.channel.send('https://regn.al/dm.png')
			return
		# ignore unknown users
		user = await self.client.db.user(message.author.id)
		if user is None: return
		# ignore AU_BANNED users
		if user.data.flags & UserFlags.AUTO_RESPONSE_BANNED: return
		# ignore bots and webhooks
		if message.author.bot or message.webhook_id: return
		# ignore empty messages
		if not message.content: return
		# parse args
		args = ArgParser(message.content)
		# validate usage of --force
		if args.force:
			if message.author.id not in self.client.owner_ids:
				create_task(self.client.au.notify_reaction(message))
			args.force = False
		# get channel, and guild
		channel = message.channel.parent if isinstance(message.channel,Thread) else message.channel
		guild = await self.client.db.guild(message.guild.id)
		if not args.force:
			# handle mode
			match guild.config.auto_responses.mode:
				case TWBFMode.disabled: return
				case TWBFMode.whitelist if channel.id not in guild.config.auto_responses.channels: return
				case TWBFMode.blacklist if channel.id in guild.config.auto_responses.channels: return
				case TWBFMode.enabled|_: pass
			# handle cooldown
			match guild.config.auto_responses.cooldown_mode:
				case AUCooldownMode.none: pass
				case AUCooldownMode.user if message.author.id in self._cooldowns: return
				case AUCooldownMode.channel if channel.id in self._cooldowns: return
				case AUCooldownMode.guild if message.guild.id in self._cooldowns: return
		await self.auto_response_handler(message,args)

	async def auto_response_handler(self,message:Message,args:ArgParser) -> None:
		# grab guild and user
		guild = await self.client.db.guild(message.guild.id)
		user = await self.client.db.user(message.author.id)
		# find matching response
		au = await self.client.au.get_response(message,args,guild.config.auto_responses.allow_cross_guild_responses)
		# if no response found, return
		if au is None: return
		# format response based on type
		followups = au.data.followups
		match au.type:
			case AutoResponseType.text: response = au.response
			case AutoResponseType.file:
				match au.id[0]:
					case 'b': response = f'https://regn.al/au/b/{quote(au.response)}'
					case 'u': response = f'https://regn.al/au/u/{au.data.guild}/{quote(au.response)}'
					case 'c': response = f'https://regn.al/au/c/{au.data.guild}/{quote(au.response)}'
					case 'm': response = f'https://regn.al/au/m/{au.data.user}/{quote(au.response)}'
					case 'p': response = f'https://regn.al/au/p/{au.data.user}/{quote(au.response)}'
					case _: return
			case AutoResponseType.script: response,followups = await self.client.au.execute_au(au.id,message)
			case _: return
		# send response
		await message.channel.send(response)
		# delete original message if --deleted
		if args.delete:
			try: await message.delete()
			except (Forbidden,NotFound,HTTPException) as e:
				self.client.log.error(f'failed to delete message by {message.author.name} in {message.guild.name}',
					guild_id=message.guild.id,metadata={'au_id':au.id,'original_deleted':args.delete,'error':str(e)})
		# create log
		self.client.log.info(f'auto response {au.id} triggered by {message.author.name} in {message.guild.name}',
			guild_id=message.guild.id,metadata={'au_id':au.id,'original_deleted':args.delete})
		# add cooldown
		create_task(self.cooldown(message.author.id,guild.config.auto_responses.cooldown))
		# add to user found if no arguments were passed
		if not args and au.id not in user.data.auto_responses.found:
			user.data.auto_responses.found.append(au.id)
			await user.save_changes()
		# send followups
		for followup in followups:
			await sleep(followup.delay)
			await message.channel.send(followup.response)


def setup(client:Client) -> None:
	client.add_cog(ExtensionAutoResponses(client))