from discord import Message,ChannelType,Member,VoiceState
from utils.db.documents.ext.flags import UserFlags
from utils.db.documents.ext.enums import TTSMode
from .subcog import ExtensionTTSSubCog
from discord.ext.commands import Cog
from asyncio import create_task


class ExtensionTTSListeners(ExtensionTTSSubCog):
	@Cog.listener()
	async def on_connect(self) -> None:
		self.text_corrections = await self.client.db.inf.text_correction()
		await self.reload_voices()

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if (
			message.guild is None or
			message.author.bot or
			message.webhook_id or
			message.content.startswith('-') or
			message.author.voice is None
		):
			return

		# ignore empty messages
		if not message.content and not message.attachments:
			return

		user_doc = await self.client.db.user(message.author.id)
		guild_doc = await self.client.db.guild(message.guild.id)
		# ignore if not in voice channel or a tts channel
		if not message.channel.id in [
			message.author.voice.channel.id,
			*guild_doc.config.tts.channels
		]:
			return
		# check user voice state
		match user_doc.config.tts.mode:
			case TTSMode.never: return
			case TTSMode.only_when_muted if (
				not message.author.voice.self_mute and
				not message.content.startswith('+')
			): return
			case TTSMode.always|_: pass
		# join channel if user has auto join, and client is not in a voice channel
		if self.guilds.get(message.guild.id,None) is None:
			if not user_doc.config.tts.auto_join:
				return
			await self.join_channel(message.author.voice.channel)
		# ensure that the client is in the correct channel
		if (
			message.guild.voice_client is None or
			message.guild.voice_client.channel.id != message.author.voice.channel.id
		):
			return
		# begin processing message
		text = message.content
		if text:
			if (
				user_doc.config.tts.mode == TTSMode.only_when_muted
				and message.content.startswith('+')
			):
				text = text.removeprefix('+')

			text = self.process_message(text,message.guild)

			if user_doc.config.tts.text_correction:
				text = self.process_text_correction(text)

		if message.attachments:
			text += (
				' along with an attachment'
				if text else
				'an attachment')
		if user_doc.config.tts.text_correction:
			await self.client.db.inf.text_correction()
		profile = await self.get_user_profile(message.author)
		if self.guilds[message.guild.id].last_name != profile.name:
			text = f'{profile.name} said: {text}'
			self.guilds[message.guild.id].last_name = profile.name
		# validate message length
		if (
			not user_doc.data.flags & UserFlags.UNLIMITED_TTS and
			len(text) > 800 or
			max({len(w) for w in text.split()}) > 64
		):
			create_task(self.client.helpers.notify_reaction(message))
			return
		# generate audio
		audio = await self.generate_audio(text,profile)
		# add message to queue
		await self.add_message_to_queue(audio,message.guild)
		# update statistics
		guild_doc.data.statistics.tts += len(text)
		await guild_doc.save_changes()

	@Cog.listener()
	async def on_voice_state_update(self,member:Member,before:VoiceState,after:VoiceState):
		if member.id == self.client.user.id and after.channel is None:
			await self.disconnect(member.guild)
			return
		if member.guild.id not in self.guilds:
			return
		if before.channel is not None:
			if (
				len(before.channel.voice_states) == 1 and
				self.client.user.id in before.channel.voice_states
			):
				await self.disconnect(member.guild)
				return
