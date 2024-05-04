from utils.db.documents import Guild as GuildDocument
from discord.errors import Forbidden,HTTPException
from discord import Guild,Member,Embed,ChannelType
from .subcog import ExtensionQOTDSubCog
from asyncio import sleep,create_task
from typing import AsyncIterator
from .views import QOTDAskLog
from .models import QOTDPack
from random import choice
from aiofiles import open
from time import time
from os import walk


class ExtensionQOTDLogic(ExtensionQOTDSubCog):
	async def reload_packs(self) -> None:
		files = next(walk('extensions/qotd/packs'),(None,None,[]))[2]
		for file in files:
			async with open(f'extensions/qotd/packs/{file}') as f:
				self.packs[file.removesuffix('.json')] = QOTDPack.model_validate_json(await f.read())

	async def remove_recently_asked(self,guild_id:int) -> None:
		await sleep(300)
		self.recently_asked.discard(guild_id)

	async def find_guilds(self) -> AsyncIterator[tuple[Guild,GuildDocument]]:
		if not self._rescan and time()-self._guilds[0] < 60:
			for guild in self._guilds[1]:
				yield guild
			return

		_client_guilds = {guild.id for guild in self.client.guilds}

		guilds = list()
		async for guild in self.client.db._client.guilds.find(
			# ensure qotd is enabled
			{'config.qotd.enabled':True,
			'config.qotd.channel':{'$ne':None}}
		):
			# ensure guild is attached to current shard and not in recently asked
			if guild['_id'] not in _client_guilds or guild['_id'] in self.recently_asked: continue
			guild = self.client.get_guild(guild['_id']) or await self.client.fetch_guild(guild['_id'])
			if guild is None: continue
			guild_doc = await self.client.db.guild(guild.id)
			# ensure guild data exists
			if guild_doc is None: continue
			# ensure asked day is not today
			if guild_doc.data.qotd.last == guild_doc.get_current_day(): continue
			guilds.append((guild,guild_doc))
			yield guild,guild_doc
		self._guilds = (time(),guilds)
		self._rescan = False

	async def log_ask_custom(self,author:Member,question:str) -> None:
		guild_doc = await self.client.db.guild(author.guild.id)
		if (
			not guild_doc.config.logging.enabled or
			guild_doc.config.logging.channel is None or
			not guild_doc.config.logging.log_commands
		): return
		channel = author.guild.get_channel(guild_doc.config.logging.channel) or await self.client.fetch_channel(guild_doc.config.logging.channel)
		if channel is None: return
		embed = Embed(description=question,color=await self.client.helpers.embed_color(author.guild.id))
		embed.set_author(name=f'{author.display_name} asked a custom question!',icon_url=author.avatar.url)
		await channel.send(embed=embed,view=QOTDAskLog(self.client))

	async def get_question(self,guild_doc:GuildDocument) -> tuple[GuildDocument,Embed]:
		embed = Embed(title='❓❔ Question of the Day ❔❓',color=await self.client.helpers.embed_color(guild_doc.id))
		if guild_doc.data.qotd.nextup:
			question = guild_doc.data.qotd.nextup.pop(0)
			embed.description = question.question
			embed.set_footer(text=f'custom question by {question.author}',icon_url=question.icon)
			return guild_doc,embed
		
		if not guild_doc.data.qotd.packs:
			raise ValueError(f'no qotd packs available for guild {guild_doc.name} ({guild_doc.id})')
		
		pack = choice(guild_doc.data.qotd.packs)
		pack_data = self.packs[pack]
		# ensure pack asked data exists
		if pack not in guild_doc.data.qotd.asked:
			guild_doc.data.qotd.asked[pack] = '0'*len(pack_data.questions)

		# ensure equal length
		if len(guild_doc.data.qotd.asked[pack]) != len(pack_data.questions):
			guild_doc.data.qotd.asked[pack] = '0'*len(pack_data.questions)
		
		asked = guild_doc.data.qotd.asked[pack]
		options = [q for i,q in enumerate(pack_data.questions) if not int(asked[i])]

		if not options:
			guild_doc.data.qotd.asked[pack] = '0'*len(pack_data.questions)
			options = pack_data
		
		embed.description = choice(options)
		index = pack_data.questions.index(embed.description)
		embed.set_footer(text=f'{pack}#{index+1}')
		guild_doc.data.qotd.asked[pack] = f'{asked[:index]}1{asked[index+1:]}' # strings are immutable
		return guild_doc,embed

	async def ask_qotd(self,guild:Guild,guild_doc:GuildDocument) -> None:
		channel = guild.get_channel(guild_doc.config.qotd.channel
			) or await self.client.fetch_channel(guild_doc.config.qotd.channel)
		if channel is None or channel.type != ChannelType.forum: return False
		_roles = [i for i in guild.roles if i.name.lower() == 'qotd' and not i.is_bot_managed()]
		ping_role = _roles[0].mention if _roles else None

		guild_doc,embed = await self.get_question(guild_doc)

		try: # archive old thread
			thread_id = guild_doc.data.qotd.last_thread
			if thread_id is not None and (old_thread:=channel.get_thread(thread_id)) is not None:
				await old_thread.edit(archived=True,locked=True,pinned=False)
		except AttributeError: pass
		except Forbidden:
			if logging_channel:=guild.get_channel(guild_doc.config.logging.channel):
				await logging_channel.send(embed=Embed(
					title='❌❗️ QOTD failed to archive thread ❗️❌',
					description=f'failed to archive thread\nplease give me the `Manage Posts` permission in <#{channel.id}>',
					color=0xff6969))

		question = embed.description
		try:
			thread = await channel.create_thread(
				name=question if len(question) <= 100 else f'{question[:97]}...',
				content=ping_role,
				embed=embed,
				auto_archive_duration=1440)
		except Forbidden:
			if logging_channel:=guild.get_channel(guild_doc.config.logging.channel):
				await logging_channel.send(embed=Embed(
					title='❌❗️ QOTD failed to create thread ❗️❌',
					description=f'failed to create thread\nplease give me the `Create Threads` permission in <#{channel.id}>',
					color=0xff6969))
			return False

		try: await thread.edit(pinned=True)
		except HTTPException:
			thread_message = await thread.fetch_message(thread.id)
			await thread_message.edit(content=f'{thread_message.content}\n\nunable to pin this thread, please unpin and archive the previous thread manually')
		self.recently_asked.add(guild.id)
		create_task(self.remove_recently_asked(guild.id))
		if not embed.footer.text.startswith('custom question'):
			metric = await self.client.db.qotd_metric(embed.footer.text)
			metric.asked += 1
			await metric.save_changes()
		self._rescan = True
		guild_doc.data.qotd.last_thread = thread.id
		guild_doc.data.qotd.last = guild_doc.get_current_day()
		guild_doc.data.statistics.questions += 1
		await guild_doc.save_changes()
		self.client.log.info(f'asked qotd in {guild.name}',guild_id=guild.id)