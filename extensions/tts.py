from discord import Message,Member,FFmpegOpusAudio,VoiceClient,VoiceState,SlashCommandGroup,ApplicationContext,Embed
from google.cloud.texttospeech import TextToSpeechAsyncClient,AudioConfig,VoiceSelectionParams,SynthesisInput
from asyncio import Queue,create_task,CancelledError,Event
from google.api_core.exceptions import InvalidArgument
from re import sub,error as RegexError
from discord.ext.commands import Cog
from os import remove as rm,scandir
from pydub import AudioSegment
from secrets import token_hex
from os.path import exists
from client import Client
from os import environ

environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_auth.json'

class guild_data:
	def __init__(self,id:int,client:Client,config:dict,vc:VoiceClient,tts:TextToSpeechAsyncClient,transcription:dict) -> None:
		self.id  = id
		self.client = client
		self.config = config
		self.tts = tts
		self.vc  = vc
		self.transcription = transcription
		self.active = None
		self.queue = Queue()
		self.playing = Event()
		self.last_user:Member = None
		self.queue_task = create_task(self.handle_queue())

	def finished_playing(self,error):
		self.playing.set()
		self.playing.clear()

	def gen_filename(self) -> None:
		filename = f'tmp/tts/{token_hex(6)}.ogg'
		while exists(filename): filename = f'tmp/tts/{token_hex(6)}.ogg'
		return filename

	async def get_user_data(self,member:Member) -> tuple[bool,str,bool,VoiceSelectionParams,AudioConfig]:
		u_config = await self.client.db.user(member.id).config.tts.read()
		g_config = await self.client.db.guild(member.guild.id).config.tts.read()
		voice    = u_config.get('voice',None) or g_config.get('voice','en-US-Neural2-H')
		return (
			u_config.get('transcription',True), # transcribe messages
			u_config.get('name',None) or member.display_name, # stated name
			g_config.get('read_name',False), # read usernames before reading message
			VoiceSelectionParams(name=voice,language_code='-'.join(voice.split('-')[:2])), # voice
			AudioConfig(audio_encoding=3,speaking_rate=u_config.get('speaking_rate',0.8)) # audio config
		)

	async def generate_audio(self,message:str,voice:VoiceSelectionParams,audio_config:AudioConfig,_last_member:Member) -> str|None:
		filename = self.gen_filename()
		with open(filename,'wb+') as file:
			try: req = await self.tts.synthesize_speech(input=SynthesisInput(text=message),voice=voice,audio_config=audio_config)
			except InvalidArgument: return False
			file.write(req.audio_content)
			file.seek(0)
			if len(AudioSegment.from_file(file,format='ogg'))/1000 > self.config.get('max_message_length',59):
				rm(filename)
				self.last_user = _last_member
				return None
		return filename

	async def play_message(self,member:Member,message:str) -> None:
		with open('/dev/null','w') as devnull:
			transcribe,username,read_name,voice,a_config = await self.get_user_data(member)
			if transcribe:
				try: message = ' '.join([sub(no_punc,self.transcription.get(no_punc,no_punc),word) for word in message.split(' ') if (no_punc:=sub(r'\,|\.','',word)) is not None])
				except RegexError: pass
			_last_member = self.last_user
			if read_name and member != self.last_user:
				message = f'{username} said: {message}'
				self.last_user = member
			for i in range(5):
				filename = await self.generate_audio(message,voice,a_config,_last_member)
				await self.client.db.guild(member.guild.id).data.tts.usage.inc(len(message))
				if filename is False: return
				if filename is not None: break
			else:
				await self.client.log.debug('tts error',member=member.id,guild=member.guild.id,message_text=message)
				return
			self.vc.play(FFmpegOpusAudio(filename,stderr=devnull),after=self.finished_playing)
			try:
				if self.vc._player: await self.playing.wait()
			except CancelledError: pass
			rm(filename)

	async def handle_queue(self) -> None:
		while True:
			try:
				if self.vc._player: self.vc._player._end.wait()
			except Exception: pass
			await self.play_message(*await self.queue.get())


class tts_cog(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.tts = TextToSpeechAsyncClient()
		self.guilds:dict[int,guild_data] = {}
		for f in scandir('tmp/tts'): rm(f.path)

	tts = SlashCommandGroup('tts','text-to-speech commands')

	def process_message(self,message:str) -> str:
		message = sub(r'(?:\~\~|\_\_\*\*\*|\_\_\*\*|\_\_\*|\_\_|\_|\*\*\*|\*\*|\*)(.*?)(?:\~\~|\*\*\*\_\_|\*\*\_\_|\*\_\_|\_\_|\_|\*\*\*|\*\*|\*)',r'\g<1>',message)
		message = sub(r'<\/((?:\w|\s)+):\d+>',r'slash \g<1> ',message)
		message = sub(r'<:(\w+):\d+>',r'\g<1>',message)
		message = sub(r'(?:^|\ )https?:\/\/(?:.*\.)?(.*)\.(?:.[^/]+)[^\s]+.',r'a \g<1> link',message)
		return message

	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if message.guild is None: return
		if (
			not getattr(message.author,'voice',None) or
			message.content.startswith('-') or
			message.content == '' or
			message.author.bot or
			message.author.id in await self.client.db.guild(message.guild.id).data.tts.banned_users.read()): return
		match await self.client.db.user(message.author.id).config.tts.mode.read():
			case 'every message': pass
			case 'only when muted' if message.author.voice.self_mute or message.author.voice.mute: pass
			case 'never'|_: return
		guild_config = await self.client.db.guild(message.guild.id).config.tts.read()
		if message.channel.id not in [message.author.voice.channel.id,guild_config.get('channel')]: return
		if message.guild.id not in self.guilds.keys():
			if not message.author.voice or not guild_config.get('auto_join',False): return
			self.guilds.update({message.guild.id:guild_data(
				message.guild.id,
				self.client,guild_config,
				message.guild.voice_client or await message.author.voice.channel.connect(),
				self.tts,await self.client.db.inf('/reg/nal').transcription.read())})
		if len(processed:=self.process_message(message.clean_content)+(', along with an attachment' if message.attachments else '')) <= 800:
			if max([len(w) for w in processed.split(' ')]) > 50: return
			self.guilds[message.guild.id].queue.put_nowait((message.author,processed))

	@Cog.listener()
	async def on_voice_state_update(self,member:Member,before:VoiceState,after:VoiceState):
		if member.id == self.client.user.id and after.channel is None:
			try: self.guilds.pop(member.guild.id)
			except KeyError: pass
		if member.guild.id not in self.guilds.keys(): return
		if before.channel is not None:
			if len(before.channel.voice_states) == 1:
				await self.guilds[member.guild.id].vc.disconnect()
				try: self.guilds.pop(member.guild.id)
				except KeyError: pass

	@tts.command(
		name='join',
		description='join current voice channel',guild_only=True)
	async def slash_tts_join(self,ctx:ApplicationContext) -> None:
		if not ctx.author.voice:
			await ctx.response.send_message(embed=Embed(title='ERROR!',description='you must be in a voice channel when running this command!',color=0xff6969))
			return
		if ctx.guild.voice_client:
			if ctx.guild.voice_client.channel.id == ctx.author.voice.channel.id:
				await ctx.response.send_message(embed=Embed(title='ERROR!',description='i am already in that channel!',color=0xff6969))
				return
		self.guilds.update({ctx.guild.id:guild_data(
				ctx.guild.id,
				self.client,await self.client.db.guild(ctx.guild.id).config.tts.read(),
				ctx.guild.voice_client or await ctx.author.voice.channel.connect(),
				self.tts,await self.client.db.inf('/reg/nal').transcription.read())})
		await ctx.response.send_message(embed=Embed(
			title='joined!',
			description=f'joined {ctx.author.voice.channel.mention}\nby default, i\'ll only read your messages if you\'re muted\nyou can change this with {[f"</{cmd.qualified_name}:{cmd.qualified_id}>" for cmd in self.client.walk_application_commands() if cmd.qualified_name == "config"][0]}\nprepend messages with "-" and i won\'t read them, regardless of config',
			color=await self.client.embed_color(ctx)),ephemeral=await self.client.hide(ctx))

	@tts.command(
		name='leave',
		description='leave the voice channel')
	async def slash_tts_leave(self,ctx:ApplicationContext) -> None:
		if not ctx.guild.voice_client:
			await ctx.response.send_message(embed=Embed(title='ERROR!',description='i am not connected to a voice channel!',color=0xff6969))
			return
		if ctx.guild.id in self.guilds.keys():
			await self.guilds[ctx.guild.id].vc.disconnect()
			try: self.guilds.pop(ctx.guild.id)
			except KeyError: pass
		else:
			await self.guilds[ctx.guild.id].vc.disconnect()
		await ctx.response.send_message(embed=Embed(
			title='disconnected!',
			description=f'have fun~',
			color=await self.client.embed_color(ctx)),ephemeral=await self.client.hide(ctx))

def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(tts_cog(client))