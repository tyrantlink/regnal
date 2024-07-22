from discord import Message,RawReactionActionEvent
from .subcog import ExtensionMediaLinkFixerSubCog
from discord.ext.commands import Cog
from discord.errors import NotFound
from regex import sub,findall
from asyncio import sleep


class ExtensionMediaLinkFixerListeners(ExtensionMediaLinkFixerSubCog):
	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if message.guild is None: return
		if message.author.bot: return
		if message.flags.suppress_embeds: return
		if not message.channel.can_send(): return

		guild_doc = await self.client.db.guild(message.guild.id)
		if not guild_doc.config.general.replace_media_links: return

		fixes = self.find_fixes(message.content)
		if not fixes: return
		fix_message = 'links converted to embed friendly urls:\n'
		clear_embeds = any((fix.clear_embeds for fix in fixes))
		for fix in fixes:
			for word in message.content.split():
				if word.startswith('http') and findall(fix.find,word):
					if fix.remove_params:
						word = word.split('?')[0]
					fix_message += f'{sub(fix.find,fix.replace,word)}\n'
		
		if clear_embeds:
			await sleep(1)
			await message.edit(suppress=True)

		self_message = await message.reply(fix_message,mention_author=False)

		await sleep(max((fix.wait_time for fix in fixes)))

		try:
			self_message = await self_message.channel.fetch_message(self_message.id)
		except NotFound:
			return
		if self_message.embeds:
			return

		await message.edit(suppress=False)
		await self_message.delete()
	
	@Cog.listener()
	async def on_raw_reaction_add(self,payload:RawReactionActionEvent) -> None:
		if (
			payload.user_id == self.client.user.id or
			payload.guild_id is None or
			payload.emoji.name != '❌'
		): return
		message = self.client.get_message(payload.message_id
			) or await self.client.get_guild(payload.guild_id
				).get_channel(payload.channel_id
				).fetch_message(payload.message_id)
		if message is None: return
		if message.reference is None: return
		if not message.content.startswith('links converted to embed friendly urls:'): return

		reference = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)

		if reference is None or reference.author.id == payload.user_id:
			await message.delete()
			if reference is not None:
				await reference.edit(suppress=False)
					
					