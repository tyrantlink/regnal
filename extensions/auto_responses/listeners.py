from discord import Cog,Message,Thread,RawReactionActionEvent
from utils.db.documents.ext.flags import UserFlags
from utils.db.documents.ext.enums import TWBFMode
from .subcog import ExtensionAutoResponsesSubCog
from asyncio import create_task
from .classes import ArgParser


class ExtensionAutoResponsesListeners(ExtensionAutoResponsesSubCog):
	@Cog.listener()
	async def on_connect(self) -> None:
		await self.client.au.reload_au()

	@Cog.listener()
	async def on_raw_reaction_add(self,payload:RawReactionActionEvent) -> None:
		if (
			payload.user_id == self.client.user.id or
			payload.guild_id is None or
			payload.emoji.name not in ['❌','❓','❔']
		): return
		message = self.client.get_message(payload.message_id
			) or await self.client.get_guild(payload.guild_id
				).get_channel(payload.channel_id
				).fetch_message(payload.message_id)
		if message is None: return
		log = await self.client.db.log(message.id)
		if log is None or (triggerer:=log.data.get('triggerer',None)) is None: return

		match payload.emoji.name: # match case because i might add more or smth idk
			case '❌' if (
				payload.user_id == triggerer or
				payload.member.guild_permissions.manage_messages or
				payload.member.id in self.client.owner_ids and self.client.project.config.dev_bypass
			):
				await message.delete()
			case _: raise ValueError(f'unknown reaction {payload.emoji.name}!')

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		# ignore bots and webhooks
		if message.author.bot or message.webhook_id: return
		# ignore dms
		if not message.guild:
			# await message.channel.send('https://regn.al/dm.png')
			return
		# ignore unknown users
		user = await self.client.db.user(message.author.id)
		if user is None: return
		# ignore users with auto responses disabled
		if not user.config.general.auto_responses: return
		# ignore AU_BANNED users
		if user.data.flags & UserFlags.AUTO_RESPONSE_BANNED: return
		# ignore empty messages
		if not message.content: return
		# parse args
		args = ArgParser(message.content)
		# validate usage of --force
		if args.force and message.author.id not in self.client.owner_ids:
			create_task(self.client.helpers.notify_reaction(message))
			args.force = False
		# get channel, and guild
		channel = message.channel.parent if isinstance(message.channel,Thread) else message.channel
		guild = await self.client.db.guild(message.guild.id)
		if not args.force:
			# handle mode
			match guild.config.auto_responses.enabled:
				case TWBFMode.false: return
				case TWBFMode.whitelist if channel.id not in guild.data.auto_responses.whitelist: return
				case TWBFMode.blacklist if channel.id in guild.data.auto_responses.blacklist: return
				case TWBFMode.true|_: pass
		await self.auto_response_handler(message,args)