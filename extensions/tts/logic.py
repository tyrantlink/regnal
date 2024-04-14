from google.cloud.texttospeech import VoiceSelectionParams,AudioConfig,AudioEncoding,SynthesisInput
from discord import Member,Guild,VoiceClient,FFmpegOpusAudio,VoiceChannel,FFmpegPCMAudio,FFmpegAudio,PCMAudio
from .models import UserTTSProfile,TTSMessage,GuildTTS
from asyncio import Queue,Event,create_task
from asyncio.subprocess import DEVNULL
from .valid_voices import valid_voices
from .subcog import ExtensionTTSSubCog
from time import perf_counter
from io import BytesIO
from re import sub


class ExtensionTTSLogic(ExtensionTTSSubCog):
	async def reload_voices(self) -> None:
		self.voices = [ #? this is super incredibly easy to read god i hate it google why
			voice
			for voice in
			[
				voice.split(':')[-1].replace('"','')
				for voice in
				[
					voice.replace(' ','').split('\n')[2]
					for voice in str(await self.tts.list_voices()).split('voices ')
					if voice
				]
				if ':' in voice
				and voice.startswith('name')
			]
		]
		valid_voices.value = set(self.voices)

	async def get_user_profile(self,user:Member) -> UserTTSProfile:
		user_doc = await self.client.db.user(user.id)
		voice = (
			user_doc.config.tts.voice or
			(await self.client.db.guild(user.guild.id)).config.tts.default_voice or
			'en-US-Neural2-H')

		return UserTTSProfile(
			name = user_doc.config.tts.name or user.display_name,
			text_correction = user_doc.config.tts.text_correction,
			voice = VoiceSelectionParams(
				language_code = '-'.join(voice.split('-')[:2]),
				name = voice),
			audio_config = AudioConfig(
				audio_encoding = AudioEncoding.OGG_OPUS,
				speaking_rate = user_doc.config.tts.speaking_rate))

	async def generate_audio(self,message:str,profile:UserTTSProfile) -> TTSMessage:
		st = perf_counter()
		req = await self.tts.synthesize_speech(
			input = SynthesisInput(
				text=message),
			voice=profile.voice,
			audio_config=profile.audio_config)
		self.client.log.debug(f'generated audio for {profile.name} in {perf_counter()-st:.2f}s')
			
		audio_data = BytesIO(req.audio_content)
		audio_data.seek(0)

		return TTSMessage(
			profile=profile,
			text=message,
			data=audio_data)

	async def add_message_to_queue(self,message:TTSMessage,guild:Guild) -> None:
		if guild.id not in self.guilds:
			raise ValueError(f'guild {guild.name} ({guild.id}) does not have a tts queue, please run create_queue')
		self.guilds[guild.id].queue.put_nowait(message)

	def process_message(self,message:str) -> str:
		# strip markdown
		message = sub(r'(?:\~\~|\_\_\*\*\*|\_\_\*\*|\_\_\*|\_\_|\_|\*\*\*|\*\*|\*)(.*?)(?:\~\~|\*\*\*\_\_|\*\*\_\_|\*\_\_|\_\_|\_|\*\*\*|\*\*|\*)',r'\g<1>',message)
		# pronounce slash commands
		message = sub(r'<\/((?:\w|\s)+):\d+>',r'slash \g<1> ',message)
		# pronounce emojis
		message = sub(r'<a?:(\w+):\d+>',r'\g<1>',message)
		# pronounce urls
		message = sub(r'(?:^|\ )<?https?:\/\/(?:.*\.)?(.*)\.(?:.[^/]+)[^\s]+.>?',r'a \g<1> link',message)
		# replace timestamps
		message = sub(r'<t:\d+(:[tTdDfFR])?>','a timestamp',message)
		return message

	def process_text_correction(self,message:str) -> str:
		return ' '.join([
			word.replace(
				punctuation_removed,
				self.text_corrections.get(
					punctuation_removed,
					punctuation_removed))
			for word in message.split(' ')
			if (punctuation_removed:=sub(r'\,|\.','',word))
			is not None])

	async def create_queue(self,guild_id:int) -> None:
		if guild_id not in self.guilds:
			self.guilds[guild_id] = GuildTTS(
				queue = Queue(),
				last_name = None)

	async def process_queue(self,guild:Guild) -> None:
		if guild.id not in self.guilds:
			await self.create_queue(guild.id)
		playing = Event()
		voice_client:VoiceClient = guild.voice_client
		while True:
			message = await self.guilds[guild.id].queue.get()
			if not voice_client.is_connected():
				voice_client = await voice_client.channel.connect()
				self.client.log.debug(f'no voice client for {guild.name} ({guild.id}), deleting queue')
				break
			playing.clear()
			voice_client.play(
				FFmpegOpusAudio(
					source = message.data,
					pipe = True,
					codec = 'opus',
					bitrate = 512,
					stderr = DEVNULL),
				after = lambda e: playing.set())
			await playing.wait()
		
		await self.disconnect(guild)

	async def join_channel(self,channel:VoiceChannel) -> None:
		voice_client:VoiceClient = channel.guild.voice_client
		if voice_client is None:
			await channel.connect()
			await self.create_queue(channel.guild.id)
			create_task(self.process_queue(channel.guild))
		elif voice_client.channel != channel:
			await voice_client.move_to(channel)

	async def disconnect(self,guild:Guild) -> None:
		if guild.voice_client is not None:
			await guild.voice_client.disconnect()
		self.guilds.pop(guild.id,None)